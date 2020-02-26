import argparse
import os
import subprocess


def run_pipeline(games_path):
    """
    Runs the pipeline of data preprocessing and model training.
    In the end models will be created in outputs folder.
    """
    basepath = os.path.dirname(os.path.realpath(__file__))
    output = os.path.join(basepath, 'outputs')
    os.makedirs(output, exist_ok=True)

    # preprocess games walkthrough
    subprocess.call(["python3",
                     os.path.join(basepath, 'datasets.py'),
                     games_path,
                     "--output", output
                     ])


if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument('games_path',
    #                     type=str,
    #                     help="path to the games files")
    # args = parser.parse_args()
    # print(args)
    # run_pipeline(args.games_path)
    game_path = r'/home/v-hapurm/Documents/Haki_Git/TextWorld/textworld/challenges/spaceship/games/levelMedium.ulx'
    run_pipeline(game_path)
