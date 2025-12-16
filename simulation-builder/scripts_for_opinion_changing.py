#######
epsilon = 0.2
current_opinions = [d.opinion for d in dreps]
num_dreps = len(dreps)
new_opinions = []
for i in range(num_dreps):
    x_i = current_opinions[i]
    close_opinions = []
    for j in range(num_dreps):
        x_j = current_opinions[j]
        if abs(x_i - x_j) <= epsilon:
            close_opinions.append(x_j)
    if close_opinions:
        average_opinion = sum(close_opinions) / len(close_opinions)
        new_opinions.append(average_opinion)
    else:
        new_opinions.append(x_i) 
for i in range(num_dreps):
    dreps[i].opinion = new_opinions[i]
########

# Deffuant-Weisbuch (DW) Model
# Parameters
epsilon = 0.2  # Confidence threshold (only interact if closer than this)
mu = 0.5       # Convergence rate (how much they move towards each other)

# Shuffle to randomize interaction order
random.shuffle(dreps)

# Pairwise interactions
for i in range(0, len(dreps) - 1, 2):
    d1 = dreps[i]
    d2 = dreps[i+1]
    
    diff = abs(d1.opinion - d2.opinion)
    
    # Only interact if opinions are close enough (within epsilon)
    if diff < epsilon:
        # Calculate shifts
        shift1 = mu * (d2.opinion - d1.opinion)
        shift2 = mu * (d1.opinion - d2.opinion)
        
        # Update opinions
        d1.opinion += shift1
        d2.opinion += shift2
        
        # Clamp to [0, 1] just in case
        d1.opinion = max(0.0, min(1.0, d1.opinion))
        d2.opinion = max(0.0, min(1.0, d2.opinion))
        
##########
# Random Walk: Each DRep moves slightly in a random direction
for d in dreps:
    # Random shift between -0.05 and +0.05
    shift = (random.random() - 0.5) * 0.1
    
    # Apply shift and keep within bounds [0, 1]
    d.opinion = max(0.0, min(1.0, d.opinion + shift))
#########