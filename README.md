B438-Checkers

A networked two-player implementation of the classic strategy game Checkers, created as a B438 class project. This project focuses on real-time client–server communication, synchronization, latency handling, and efficient game-state transmission.

📌 Project Overview

The goal of this project is to design and implement a fully playable, networked Checkers game that allows two players to connect over a network and take turns in real time. While Checkers has simple mechanics, this project emphasizes network programming concepts including:

Synchronization across two remote clients

Latency management

Efficient and minimal game-state updates

Handling turn-based fairness

Ensuring consistency between game clients

This repository contains the implementation, documentation, and research analysis required for the B438 final project.

🎮 Features

Two-player Checkers with full rules

Real-time networked gameplay

Client–server architecture

Move validation and enforced turn-taking

Synchronized board state between clients

Comparison of networking strategies:

Raw state transmission

Compressed/optimized state updates

📡 Networking Design

This project investigates and implements multiple approaches to multiplayer networking, including:

TCP/UDP socket communication

State synchronization models

Latency handling and mitigation

Reducing unnecessary network traffic

Ensuring fairness in turn-based interactions

These networking techniques are evaluated and compared as part of the project's research component.

📚 Research Component

Alongside the implementation, the project includes a literature-based analysis of:

Techniques used in multiplayer games

Strategies for synchronization and prediction

Latency compensation

Data compression for game state updates

The final paper connects these topics to our implemented networking system.

🛠️ Tools & Technologies

Python

TCP/UDP sockets

Compatible Python IDE

Git for version control

Testing and debugging tools
