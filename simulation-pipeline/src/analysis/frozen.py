import pandas as pd
from pathlib import Path
from src.analysis.utils import assign_closest_dreps_df # Import the shared function

def run_frozen_analysis(config):
    """
    Builds CSV outputs where delegations are "frozen" from the first epoch
    a delegator is seen.
    (Converted from build_frozen_delegations.ipynb)
    """
    
    # Load inputs
    try:
        dreps = pd.read_csv(config.DREPS_STATE_FILE)
        deleg = pd.read_csv(config.DELEGATORS_STATE_FILE)
    except FileNotFoundError:
        print(f"❌ Error: Input files not found in '{config.DATA_DIR_RAW}'.")
        print("👉 Run the --simulate step first.")
        return

    # First seen epoch per delegator
    first_seen = deleg.groupby('delegator_id', as_index=False)['epoch'].min().rename(columns={'epoch':'first_epoch'})
    deleg = deleg.merge(first_seen, on='delegator_id', how='left')

    dreps['drep_id'] = dreps['drep_id'].astype(str)
    deleg['delegator_id'] = deleg['delegator_id'].astype(str)

    epochs = sorted(dreps['epoch'].unique())

    frozen_map = {}
    delegator_rows = []
    drep_rows = []

    for e in epochs:
        D = dreps.loc[dreps['epoch'] == e, ['drep_id','opinion','stake']].copy()
        A = deleg.loc[deleg['epoch'] == e, ['delegator_id','opinion','stake','s','first_epoch']].copy()
        
        if A.empty or D.empty:
            print(f"  Skipping epoch {e} (no agents).")
            continue

        # Freeze mapping at first seen epoch
        new_ids = [aid for aid, fe in zip(A['delegator_id'], A['first_epoch']) if (aid not in frozen_map) and (fe == e)]
        if new_ids:
            Ae_new = A[A['delegator_id'].isin(new_ids)][['delegator_id','opinion']].copy()
            nearest_new = assign_closest_dreps_df(Ae_new, D)
            for _, row in nearest_new.iterrows():
                frozen_map[row['delegator_id']] = row['drep_id']

        # Fallback: if any still unassigned (data quirks), assign now
        missing = [aid for aid in A['delegator_id'] if aid not in frozen_map]
        if missing:
            Ae_new = A[A['delegator_id'].isin(missing)][['delegator_id','opinion']].copy()
            nearest_new = assign_closest_dreps_df(Ae_new, D)
            for _, row in nearest_new.iterrows():
                frozen_map[row['delegator_id']] = row['drep_id']

        # Build per-delegator rows for epoch e
        map_df = pd.DataFrame({'delegator_id': list(A['delegator_id']), 'drep_id': [frozen_map.get(aid) for aid in A['delegator_id']]}).astype(str)
        D_op = D[['drep_id','opinion']].rename(columns={'opinion':'drep_opinion'})
        joined = A.merge(map_df, on='delegator_id', how='left').merge(D_op, on='drep_id', how='left')
        joined['distance'] = (joined['opinion'] - joined['drep_opinion']).abs()

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

        all_ids = list(D['drep_id'])
        total_Wprime = 0.0
        tmp = []
        for d_id in all_ids:
            del_st = float(delegated_stake.get(d_id, 0.0))
            own_st = float(own.get(d_id, 0.0))
            Wp = own_st + del_st
            total_Wprime += Wp
            tmp.append({
                'epoch': int(e),
                'drep_id': d_id,
                'opinion': float(D.loc[D['drep_id']==d_id, 'opinion'].iloc[0]),
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
    pd.DataFrame(delegator_rows).to_csv(config.DELEGATORS_FROZEN_FILE, index=False)
    pd.DataFrame(drep_rows).to_csv(config.DREPS_FROZEN_FILE, index=False)

    print(f"  Saved frozen delegator state: {config.DELEGATORS_FROZEN_FILE.name}")
    print(f"  Saved frozen DRep state: {config.DREPS_FROZEN_FILE.name}")
