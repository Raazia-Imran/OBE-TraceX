from pathlib import Path
from django.core.management.base import BaseCommand
from evaluations.reports import populate, render_pdf
from evaluations.rubrics import RUBRICS, STAGES
class Command(BaseCommand):
    help = 'Generate clearly named synthetic template verification samples. Never imports student data.'
    def add_arguments(self, parser): parser.add_argument('--output', required=True)
    def handle(self, *args, **options):
        folder = Path(options['output']); folder.mkdir(parents=True, exist_ok=True)
        for stage in (*STAGES, 'D7'):
            students=[]
            for i in range(4):
                s={'seat': f'SE-9900{i+1}', 'name': f'Sample Student {i+1}', 'total': '200' if stage=='D7' else str(sum(RUBRICS[stage]['maxima']))}
                if stage=='D7': s['stages']=['12','20','48','48','32','40']
                else: s['criteria']=[str(x) for x in RUBRICS[stage]['maxima']]
                students.append(s)
            content = populate(stage, {'project_id':'SAMPLE-ONLY','project_title':'Template verification sample',
                              'course_code':'SAMPLE', 'students': students})
            (folder / f'SAMPLE_ONLY_{stage}.docx').write_bytes(content)
            (folder / f'SAMPLE_ONLY_{stage}.pdf').write_bytes(render_pdf(content))
        self.stdout.write('Seven synthetic Word/PDF samples generated. These are not approved academic records.')
