# Connect4
A simple Connect 4 game where you can play against one good, medium and bad ai, each at different difficulties. Web mode only has one AI.

You can play Web mode here and try to beat the UCB Algorithm or play with a friend: https://kazamir.itch.io/connect-4

## Features
- Player V Player
- Player V Algorithmn
  - 3 Algorithms -> UCB search, Monte Carlo Tree search (MCTS) and AlphaZero style (DMCTS)

## How to play locally

To play with the full 3 algorithms, click the green **Code** button at the top of this page, **Download ZIP** to extract it. Open a terminal inside the extracted folder, run `pip install -r requirements.txt`, then run `python Connect4_v6.py` to start the game. You need python 3.10 or newer to play.

## How it works

The game is built in pygame, a python software for game development. The most technical part of the project is in the computer algorithms. While UCB is a relatively simple algorithm, MCTS is a tree based desicion making model and DMCTS is an AI deep learning algorithmn made using Pytorch. While DMCTS is capable of producing large and powerful AI's, the version I made was not the smartest desplite the hours I spent training and iterating on it. All in all, this is the 7th iteration of the intiall connect 4 project I began at the start of stardance.

## Credits

Credit to Pytorch, Pygame-ce and Gemini for teaching me how to use pygame and upload a web version. Most credit to Prof Mihai Nica on Youtube for teaching me the concepts behind the AIs.
