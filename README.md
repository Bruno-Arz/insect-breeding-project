# Selective Breeding Simulation MVP

Simulation-based insect (Black Soldier Fly / Mealworm) quantitative genetics selective breeding model.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the 15-generation simulation demo:
   ```bash
   python main.py
   ```

3. Run automated unit tests:
   ```bash
   python run_tests.py
   ```

## Project Structure

- `config.py`: Simulation and biological parameters.
- `main.py`: Main orchestrator script.
- `run_tests.py`: Standard python test runner.
- `simulation/`: Population pedigree structure and trait inheritance engine.
- `genetics/`: Heritability (ANOVA) and breeding value (EBV) estimation.
- `selection/`: Truncation selection and nested mating modules.
- `metrics/`: Breeder's equation gain and inbreeding calculator.
- `visualization/`: Matplotlib plotting module.
- `tests/`: Pytest / unittest suite.
- `output/`: Generated CSV data log and PNG figures.
