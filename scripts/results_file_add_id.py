import pandas as pd
import os 
from llm_epanet.utils.utils import get_results_dir
from llm_epanet.data.queries import get_queries

results_dir = get_results_dir()
# result_files = sorted(os.listdir(results_dir))[1:]
result_files = [f for f in os.listdir(results_dir) if f.endswith('.csv')]
print(result_files[::-1])

for file in result_files:
    print(file)
    df_io = pd.read_csv(os.path.join(results_dir, file))
    if 'id' in df_io.columns:
        print(f"'id' column already exists in {file}, skipping...")
        continue
    df = df_io.copy()
    df

    mapping = ([(e['prompt'].format(**e['args']), e['id'], e['network'].split('/')[-1]) for e in get_queries(['all'])])
    mapping = {(q, n): id for q, id, n in mapping}
    print(mapping)

    # query_to_id = dict([(e['prompt'], e['id']) for e in get_queries(['all'])])
    df['id'] = df.set_index(['query', 'network']).index.map(mapping).values
    df = df[['id'] + [col for col in df.columns if col != 'id']]
    df.to_csv(os.path.join(results_dir, file), index=False)
# for i in df.index:
    # df['id'].iloc[i] = [el[0] for el in  if el[1] == df['query'].iloc[i]]