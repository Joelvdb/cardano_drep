import argparse
import importlib
from pathlib import Path

# --- Import your pipeline functions ---
from src.simulation.run_simulation import execute_simulation
from src.analysis.optimal import run_optimal_analysis
from src.analysis.frozen import run_frozen_analysis
from src.analysis.probabilistic import run_probabilistic_analysis
from src.proposals.simulate_votes import run_proposal_simulation
from src.plotting.comparative_plots import run_plotting

# --- Analysis "Plugin" Map ---
# This map makes it easy to add new analysis types
ANALYSIS_MODELS = {
    "optimal": run_optimal_analysis,
    "frozen": run_frozen_analysis,
    "probabilistic": run_probabilistic_analysis,
}

def get_config(config_name: str):
    """Dynamically imports a config file from the configs/ directory."""
    try:
        # Add 'configs' to sys.path to ensure it's found
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        config_module = importlib.import_module(f"configs.{config_name}")
        print(f"✅ Loaded configuration: 'configs/{config_name}.py'")
        return config_module
    except ImportError as e:
        print(f"❌ Error: Config file 'configs/{config_name}.py' not found.")
        print(f"👉 Make sure the file exists and has no syntax errors.")
        print(f"Details: {e}")
        exit(1)
    finally:
        # Clean up sys.path
        if 'sys' in locals() and str(Path(__file__).resolve().parent) in sys.path:
            sys.path.pop(0)

def main():
    parser = argparse.ArgumentParser(description="Run the DRep Simulation Pipeline")
    
    parser.add_argument(
        "--config",
        type=str,
        default="base_config",
        help="The name of the config file to use (e.g., 'base_config' or 'experiment_high_stake')."
    )
    
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run Step 1: Generate raw simulation data."
    )
    
    parser.add_argument(
        "--analyze",
        nargs="+",  # Accepts one or more values
        choices=list(ANALYSIS_MODELS.keys()) + ["all"],
        help=f"Run Step 2: Run one or more analysis models. Choices: {list(ANALYSIS_MODELS.keys())} or 'all'"
    )
    
    parser.add_argument(
        "--proposals",
        action="store_true",
        help="Run Step 3: Simulate proposal voting on analysis results."
    )
    
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Run Step 4: Generate plots from the analysis results."
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all steps in order: simulate, analyze (all), proposals, plot."
    )
    
    args = parser.parse_args()
    
    # --- Load Config ---
    # We need to add the project root to sys.path for configs and src to be importable
    import sys
    project_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(project_root))
    
    try:
        config_module = importlib.import_module(f"configs.{args.config}")
        print(f"✅ Loaded configuration: 'configs/{args.config}.py'")
    except ImportError as e:
        print(f"❌ Error: Config file 'configs/{args.config}.py' not found.")
        print(f"👉 Make sure the file exists and has no syntax errors.")
        print(f"Details: {e}")
        exit(1)

    # --- Determine which steps to run ---
    run_simulate = args.simulate or args.all
    run_analyze = args.analyze or args.all
    run_proposals = args.proposals or args.all
    run_plot = args.plot or args.all
    
    if not any([run_simulate, run_analyze, run_proposals, run_plot]):
        print("🔔 No steps selected. Use --help to see options.")
        return

    # --- Execute Pipeline Steps ---
    
    if run_simulate:
        print("\n--- 1. Running Simulation ---")
        config_module.create_directories() # Ensure dirs exist
        execute_simulation(config_module)


    if run_analyze:
        print("\n--- 2. Running Analysis ---")
        config_module.create_directories() # Ensure dirs exist
        
        models_to_run = []
        if args.all:
            models_to_run = ANALYSIS_MODELS.keys()
        elif args.analyze:
            if "all" in args.analyze:
                models_to_run = ANALYSIS_MODELS.keys()
            else:
                models_to_run = args.analyze
        
        for model_name in models_to_run:
            if model_name in ANALYSIS_MODELS:
                print(f"Running analysis model: '{model_name}'...")
                analysis_func = ANALYSIS_MODELS[model_name]
                analysis_func(config_module)
        print("✅ Analysis complete.")

    if run_proposals:
        print("\n--- 3. Running Proposal Simulation ---")
        config_module.create_directories() # Ensure dirs exist
        run_proposal_simulation(config_module)
        print("✅ Proposal simulation complete.")

    if run_plot:
        print("\n--- 4. Generating Plots ---")
        config_module.create_directories() # Ensure dirs exist
        run_plotting(config_module)
        print("✅ Plotting complete.")

    print("\n🎉 Pipeline finished.")
    
    # Clean up sys.path
    if str(project_root) in sys.path:
        sys.path.pop(0)

if __name__ == "__main__":
    main()
