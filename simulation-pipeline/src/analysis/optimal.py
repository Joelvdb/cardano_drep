import pandas as pd
from pathlib import Path
from src.analysis.utils import assign_closest_dreps_df # Import the shared function

def run_optimal_analysis(config):
    """
    Assigns, for each epoch, each delegator to the *closest* DRep by opinion.
    (Converted from build_states_with_delegations_and_wprime_optimal.ipynb)
    """
    
    # Load inputs
    try:
        dreps = pd.read_csv(config.DREPS_STATE_FILE)
        deleg = pd.read_csv(config.DELEGATORS_STATE_FILE)
    except FileNotFoundError:
        print(f"❌ Error: Input files not found in '{config.DATA_DIR_RAW}'.")
        print("👉 Run the --simulate step first.")
        return

    delegator_rows = []
    drep_rows = []
    epochs = sorted(dreps['epoch'].unique())

    for e in epochs:
        D = dreps.loc[dreps['epoch'] == e, ['drep_id','opinion','stake']].copy()
        A = deleg.loc[deleg['epoch'] == e, ['delegator_id','opinion','stake','s']].copy()

        if A.empty or D.empty:
            print(f"  Skipping epoch {e} (no agents).")
            continue
            
        nearest = assign_closest_dreps_df(A, D)
        joined = (A.merge(nearest, on='delegator_id', how='left'))

        # Delegator rows
        for _, r in joined.iterrows():
            delegator_rows.append({
                'epoch': int(e),
                'delegator_id': r['delegator_id'],
                'opinion': float(r['opinion']),
                'stake': float(r['stake']),
                's': float(r['s']),
                'drep_id': r['drep_id'],
                'drep_opinion': float(r['drep_opinion']),
                'distance': float(r['distance']),
            })

        # DRep aggregates
        own = dict(zip(D['drep_id'], D['stake']))
        delegated_stake = joined.groupby('drep_id')['stake'].sum().to_dict()
        indeg = joined.groupby('drep_id')['delegator_id'].count().to_dict()
        avgdist = joined.groupby('drep_id')['distance'].mean().to_dict()

        total_Wprime = 0.0
        tmp = []
        for d_id, op in zip(D['drep_id'], D['opinion']):
            del_st = float(delegated_stake.get(d_id, 0.0))
            own_st = float(own.get(d_id, 0.0))
            Wp = own_st + del_st
            total_Wprime += Wp
            tmp.append({
                'epoch': int(e),
                'drep_id': d_id,
                'opinion': float(op),
                'stake': own_st,
                'delegated_stake': del_st,
                'indegree': int(indeg.get(d_id, 0)),
                'avg_distance': float(avgdist.get(d_id, 0.0)),
                'Wprime': Wp,
            })
            
        for row in tmp:
            row['Wprime_share'] = (row['Wprime'] / total_Wprime) if total_Wprime > 0 else 0.0
            drep_rows.append(row)

    # Save outputs
    pd.DataFrame(delegator_rows).to_csv(config.DELEGATORS_OPTIMAL_FILE, index=False)
    pd.DataFrame(drep_rows).to_csv(config.DREPS_OPTIMAL_FILE, index=False)

    print(f"  Saved optimal delegator state: {config.DELEGATORS_OPTIMAL_FILE.name}")
    print(f"  Saved optimal DRep state: {config.DREPS_OPTIMAL_FILE.name}")
