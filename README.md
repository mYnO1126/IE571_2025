# IE571_2025 War Game Modeling
### KAIST IE571 2025 Spring 
Group 2 김희연, 민향숙, 신희연, 양승부, 이민호, 정민혁

## War Game

### Scenario
Valley of Tears, Yom Kippur War, 1973 Arab-Israeli War

### Installation 

Clone repo and install [requirements.txt](git@github.com:mYnO1126/IE571_2025.git) in a
[**Python>=3.12**](https://www.python.org/) environment.

Python 3.13.3 used for simulation.

Follow the steps below in order to reproduce the results.


1. Clone repo

```bash
git clone https://github.com/mYnO1126/IE571_2025.git  # clone
cd IE571_2025
```

2.  Make a Conda Environment
    <details>
        <summary>Install Conda if necessary</summary>
        Install Conda that fits with your machine

        ```bash
        wget https://repo.anaconda.com/archive/Anaconda3-2024.02-1-Linux-x86_64.sh
        bash Anaconda3-2024.02-1-Linux-x86_64.sh
        conda init
        ```

    </details>

```bash
conda create -n wargame python=3.13
conda activate wargame
```

3. Install Requirements

```bash
pip install -r requirements.txt  # install
```

### Run War Game Simulation

```bash
python main.py
```

results saved in res/res"i"

