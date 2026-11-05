"""Import the existing workbook's calculated results without replacing its grading engine."""
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from .models import ImportBatch, MasterRecord, ProjectGroup, FrozenResult
from .rubrics import STAGES, RUBRICS, number, percentage, seat_number, weighted, display
from .services import audit, digest, require
from .importers import RAW_TABS, clean_rows, criterion_columns
MASTER_TAB = ' D7_CONSOLIDATED_GRADING'
AVERAGED = {'D1':'D1_Averaged_QEC','D3':'D3_Averaged_QEC','D5':'D5_Averaged_QEC','D6':'D6_Averaged_QEC'}
SCORE_HEADERS = ['Proposal (12)','S1 Progress (20)','S1 Eval (48)','S2 Progress (48)','Final Report (32)','Final Eval (40)']
READ_TABS = [MASTER_TAB, *AVERAGED.values(), *RAW_TABS.values()]

def index_rows(values):
    indexed = {}
    for row in clean_rows(values):
        raw = row.get('Seat Number', row.get('Seat Number / Roll Number'))
        if not raw: continue
        key = seat_number(raw)
        indexed.setdefault(key, []).append(row)
    return indexed

@transaction.atomic
def import_master(tabs, session, actor, source_digest):
    require(actor, ['coordinator'])
    source = tabs.get(MASTER_TAB) or tabs.get(MASTER_TAB.strip())
    if not source: raise ValueError('The consolidated D7 master tab is missing.')
    rows = index_rows(source)
    details = {stage:index_rows(tabs.get(tab, [])) for stage,tab in AVERAGED.items()}
    raw = {stage:index_rows(tabs.get(tab, [])) for stage,tab in RAW_TABS.items()}
    summary = {'accepted':0,'held':0,'unchanged':0,'issues':[], 'source':'existing calculated master workbook'}
    groups = list(ProjectGroup.objects.select_for_update().filter(session=session).order_by('pk'))
    for group in groups:
        if FrozenResult.objects.filter(group=group,stage='FINAL',active=True).exists():
            summary['held'] += group.students.count()
            summary['issues'].append(f'{group.project_id}: frozen records preserved. HOD must reopen before importing changes.')
            continue
        for student in group.students.all():
            matches = rows.get(student.seat, [])
            if len(matches)!=1:
                summary['issues'].append(f'{student.seat}: expected one consolidated row, found {len(matches)}.')
                # Never leave a previously imported row looking fresh after a missing/duplicate source.
                old=MasterRecord.objects.filter(student=student).first()
                if old:
                    old.errors=['ALL: consolidated source row missing or duplicated.'];old.save()
                continue
            row=matches[0]; errors=[]; stages={}
            for stage,header in zip(STAGES,SCORE_HEADERS):
                try:
                    total=number(row.get(header))
                    if not 0<=total<=sum(RUBRICS[stage]['maxima']): raise ValueError('Stage total outside its allowed range.')
                    criteria=[]
                    if stage in AVERAGED:
                        found=details[stage].get(student.seat,[])
                        if len(found)!=1: raise ValueError('Missing or duplicated averaged criterion row.')
                        criterion_headers=[h for h in found[0] if h.startswith('Avg ')]
                        criteria=[number(found[0][h]) for h in criterion_headers]
                    else:
                        found=raw[stage].get(student.seat,[])
                        if len(found)!=1: raise ValueError('Supervisor criterion detail is missing or repeated; resolve the source before official export.')
                        columns=criterion_columns(stage,list(found[0]))
                        criteria=weighted(stage,[percentage(found[0].get(h)) for h in columns])
                    if len(criteria)!=len(RUBRICS[stage]['maxima']): raise ValueError('Criterion columns are incomplete.')
                    if any(not 0<=v<=m for v,m in zip(criteria,RUBRICS[stage]['maxima'])): raise ValueError('Criterion mark outside its maximum.')
                    if abs(sum(criteria)-total)>Decimal('.005'):
                        raise ValueError(f'Master total {total} disagrees with criterion detail {sum(criteria)}. Source unchanged; faculty reconciliation required.')
                    stages[stage]={'criteria':[str(x) for x in criteria],'total':str(total),'display_total':display(total)}
                except ValueError as error: errors.append(f'{stage}: {error}')
            for frozen in FrozenResult.objects.filter(group=group,active=True):
                approved=next((x for x in frozen.payload.get('students',[]) if x['seat']==student.seat),None)
                incoming=stages.get(frozen.stage)
                if approved and incoming and (approved['total']!=incoming['total'] or approved['criteria']!=incoming['criteria']):
                    errors.append(f'{frozen.stage}: source changed after freezing; HOD reopening required.')
            final=None
            try:
                final=number(row.get('TOTAL (200)'))
                if not 0<=final<=200: raise ValueError('Final total outside 0–200.')
                if len(stages)==6:
                    exact=sum(number(x['total']) for x in stages.values())
                    rounded=exact.quantize(Decimal('1'),rounding=ROUND_HALF_UP)
                    if abs(final-exact)>Decimal('.005') and final!=rounded:
                        raise ValueError('Final master total does not reconcile to stage totals or whole-total rounding.')
            except ValueError as error:errors.append(f'FINAL: {error}')
            payload={'stages':stages,'final':str(final) if final is not None else None,
                     'reported_stages':{s:str(row.get(h,'')) for s,h in zip(STAGES,SCORE_HEADERS)},
                     'source':'master_workbook','source_digest':source_digest}
            content_digest=digest(payload)
            record=MasterRecord.objects.filter(student=student).first()
            if record and record.digest==content_digest and record.errors==errors:summary['unchanged']+=1
            else:
                MasterRecord.objects.update_or_create(student=student,defaults={'payload':payload,'digest':content_digest,'errors':errors})
                group.version+=1;group.save(update_fields=['version']);summary['accepted']+=1
            summary['issues'].extend(f'{student.seat} {error}' for error in errors)
    known={s.seat for g in groups for s in g.students.all()}
    summary['issues'].extend(f'{seat}: not in this session’s official roster.' for seat in rows if seat not in known)
    ImportBatch.objects.create(session=session,digest=source_digest,summary=summary,created_by=actor)
    audit(actor,'master.synced',session.pk,{'accepted':summary['accepted'],'issues':len(summary['issues'])})
    return summary

def master_stage_result(group, stage):
    errors=[]; students=[]
    if not group.session.rules_approved:errors.append('HOD must approve the source-workbook and reporting policy.')
    if group.students.count()!=group.expected_members:errors.append('Registered group membership is incomplete.')
    for student in group.students.all():
        record=MasterRecord.objects.filter(student=student).first()
        if not record:errors.append(f'{student.seat}: master data not imported.');continue
        errors.extend(f'{student.seat}: {x}' for x in record.errors if x.startswith((stage+':','ALL:')))
        value=record.payload['stages'].get(stage)
        if value:students.append({'seat':student.seat,'name':student.name,**value,'evaluators':'Source sheet','revision_ids':[], 'master_digest':record.digest})
    return {'stage':stage,'ruleset':'existing-master-workbook','project_id':group.project_id,'project_title':group.title,
            'session':group.session.label,'course_code':group.session.course_code,'attempt':group.attempt,
            'students':students,'errors':errors,'source':'master_workbook'}
