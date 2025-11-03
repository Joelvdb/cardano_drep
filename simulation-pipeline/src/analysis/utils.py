import pandas as pd

def assign_closest_dreps_df(Ae: pd.DataFrame, De: pd.DataFrame) -> pd.DataFrame:
    """
    Assigns each delegator in DataFrame Ae to the closest DRep in DataFrame De.
    
    Returns a DataFrame with [delegator_id, drep_id, drep_opinion, distance].
    """
    a = Ae[['delegator_id','opinion']].rename(columns={'opinion':'op_a'}).copy()
    d = De[['drep_id','opinion']].rename(columns={'opinion':'op_d'}).copy()
    
    a['key'] = 1
    d['key'] = 1
    
    pairs = a.merge(d, on='key').drop(columns=['key'])
    pairs['distance'] = (pairs['op_a'] - pairs['op_d']).abs()
    
    # Sort by distance, then drep_id (as a tie-breaker)
    nearest = (pairs.sort_values(['delegator_id','distance','drep_id'])
                    .groupby('delegator_id', as_index=False)
                    .first())
                    
    nearest = nearest.rename(columns={'op_d':'drep_opinion'})
    
    return nearest[['delegator_id','drep_id','drep_opinion','distance']]
