import json

def cmp(arg1):
    return arg1['instances']

with open("trial_results.json", "r") as f:
    data = json.loads(f.read())
missing = data['errors']['INVALID_COMMAND']
for obj in missing:
    del obj['examples']
missing = sorted(missing, key=cmp, reverse=True)

for i, obj in enumerate(missing[:11]):
    print(f"{i}:", obj)
