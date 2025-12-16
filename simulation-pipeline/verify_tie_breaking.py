import sys
import os
import random

# Add the current directory to sys.path to allow importing src
sys.path.append(os.getcwd())

from src.simulation.models import DRep, Delegator

def test_tie_breaking():
    print("Testing Tie-Breaking Logic...")
    
    # Setup: Two DReps with identical opinion (0.5)
    # ID "B" is lexicographically > "A". 
    # Default max() behavior would pick "B" if utilities are equal.
    drep_a = DRep(id="A", opinion=0.5, stake=100)
    drep_b = DRep(id="B", opinion=0.5, stake=100)
    
    dreps = [drep_a, drep_b]
    
    # Case 1: Delegator is currently assigned to "A".
    # Should stay with "A" despite "B" being "better" by ID.
    delegator = Delegator(id="del1", opinion=0.5, stake=10, s=0.0, current=drep_a)
    
    best = delegator.find_best_drep(dreps)
    print(f"Current: A, Best found: {best.id}")
    
    if best.id != "A":
        print("FAIL: Should have stayed with A")
        return False
        
    # Case 2: Delegator is currently assigned to "B".
    # Should stay with "B".
    delegator.current = drep_b
    best = delegator.find_best_drep(dreps)
    print(f"Current: B, Best found: {best.id}")
    
    if best.id != "B":
        print("FAIL: Should have stayed with B")
        return False

    # Case 3: Delegator is unassigned (None).
    # Should pick "B" (default max behavior).
    delegator.current = None
    best = delegator.find_best_drep(dreps)
    print(f"Current: None, Best found: {best.id}")
    
    if best.id != "B":
        print("FAIL: Should have picked B (lexicographically max)")
        return False

    # Case 4: Strictly better option exists.
    # DRep C with opinion 0.5 (perfect match), but let's say others are 0.4.
    # Wait, let's make others 0.4 so C is strictly better.
    drep_a.opinion = 0.4
    drep_b.opinion = 0.4
    drep_c = DRep(id="C", opinion=0.5, stake=100)
    dreps = [drep_a, drep_b, drep_c]
    
    delegator.opinion = 0.5
    delegator.current = drep_a # Assigned to worse DRep
    
    best = delegator.find_best_drep(dreps)
    print(f"Current: A (0.4), C (0.5) exists. Best found: {best.id}")
    
    if best.id != "C":
        print("FAIL: Should have switched to C")
        return False

    print("SUCCESS: All tie-breaking tests passed.")
    return True

if __name__ == "__main__":
    success = test_tie_breaking()
    if not success:
        sys.exit(1)
