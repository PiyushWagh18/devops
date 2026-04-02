import urllib.request, json, time

PAT = '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'
REPO = 'PiyushWagh18/devops'
headers = {'Authorization': f'token {PAT}', 'Accept': 'application/vnd.github.v3+json'}

def api(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

start = time.time()

for attempt in range(60):
    time.sleep(10)
    runs = api(f'https://api.github.com/repos/{REPO}/actions/runs?per_page=3')
    if runs['workflow_runs']:
        run = runs['workflow_runs'][0]
        run_id = run['id']
        status = run['status']
        conclusion = run['conclusion'] or 'running'

        jobs = api(f'https://api.github.com/repos/{REPO}/actions/runs/{run_id}/jobs')
        job_summary = ' | '.join([f"{j['name']}:{j['conclusion'] or j['status']}" for j in jobs['jobs']])

        elapsed = int(time.time() - start)
        print(f'[{elapsed}s] {status}/{conclusion}: {job_summary}')

        if status == 'completed':
            print(f'\nPipeline finished: {conclusion}')
            if conclusion != 'success':
                # Print deploy job logs
                for j in jobs['jobs']:
                    if j['name'] == 'deploy' and j['conclusion'] != 'success':
                        steps = api(f"https://api.github.com/repos/{REPO}/actions/jobs/{j['id']}")
                        print('\nDeploy job steps:')
                        for s in steps.get('steps', []):
                            print(f"  {s['name']}: {s['conclusion'] or s['status']}")
            break
