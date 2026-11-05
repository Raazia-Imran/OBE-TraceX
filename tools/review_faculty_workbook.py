"""Read the historical faculty reference only; never submit forms or alter source marks."""
import csv
import json
import sys
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import openpyxl


def review(source):
    workbook=openpyxl.load_workbook(source,read_only=True,data_only=True)
    sheet=workbook.active
    if sheet['G6'].value != "Student's Roll No" or sheet['EY4'].value != 'Final Marks':
        raise ValueError('This is not the reviewed faculty reference layout.')
    stages={'D1':('AD','AE'),'D2':('BR','BS'),'D3':('BH','BI'),'D4':('EV','EW'),'D5':('DI','DJ'),'D6':('EJ','EK')}
    group=title=None;students=[]
    for row in range(7,sheet.max_row+1):
        if sheet[f'D{row}'].value:
            group=str(sheet[f'D{row}'].value).strip();title=str(sheet[f'E{row}'].value).strip()
        seat=sheet[f'G{row}'].value
        if not seat:continue
        raw={stage:str(sheet[f'{columns[0]}{row}'].value) for stage,columns in stages.items()}
        reported={stage:str(sheet[f'{columns[1]}{row}'].value) for stage,columns in stages.items()}
        expected=Decimal(str(sheet[f'EY{row}'].value))
        stage_sum=sum(Decimal(v) for v in reported.values())
        whole_round=sum(Decimal(v) for v in raw.values()).quantize(Decimal('1'),rounding=ROUND_HALF_UP)
        students.append({'source_row':row,'seat':str(seat).strip(),'name':str(sheet[f'F{row}'].value).strip(),
                         'project_id':group,'project_title':title,'raw_stages':raw,'reported_stages':reported,
                         'expected_total':str(expected),'stage_sum_matches':stage_sum==expected,
                         'whole_total_rounding_matches':whole_round==expected})
    workbook.close()
    return {'source':Path(source).name,'students':students,'rounding':'D1/D2/D3/D4/D6: stage ROUND(0); D5: CEILING(1); final: sum of reported stages.',
            'groups':len(set(x['project_id'] for x in students))}


if __name__=='__main__':
    result=review(sys.argv[1]);destination=Path(sys.argv[2]);destination.mkdir(parents=True,exist_ok=True)
    (destination/'faculty-reference-review.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    with (destination/'faculty-reference-roster.csv').open('w',newline='',encoding='utf-8') as file:
        columns=['seat','name','project_id','project_title','expected_members','attempt'];writer=csv.DictWriter(file,fieldnames=columns);writer.writeheader()
        for student in result['students']:
            writer.writerow({**{key:student[key] for key in columns[:4]},'expected_members':sum(x['project_id']==student['project_id'] for x in result['students']),'attempt':1})
    print('Reference students:',len(result['students']),'groups:',result['groups'])
    print('Stage sums reconcile:',all(x['stage_sum_matches'] for x in result['students']))
    print('Students differing from whole-total rounding:',sum(not x['whole_total_rounding_matches'] for x in result['students']))
    print('Private review and roster saved. No live source or portal record changed.')
