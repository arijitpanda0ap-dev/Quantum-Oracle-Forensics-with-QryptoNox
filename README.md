# Quantum Oracle Forensics with QryptoNox

## Project Overview
This project is a Python/Qiskit prototype for identifying the family of a sealed, noisy quantum oracle and recovering its secret where applicable.

## Requirements
- Python 3.10 or newer, subject to the official challenge requirements
- Qiskit 2.x
- NumPy
- SciPy

## Installation
Install the required packages:

bash
python -m pip install -r requirements.txt


## Basic Execution Test
Run:

bash
python test_solver.py


The current test uses a mock callback that returns fabricated measurement counts. It verifies basic execution and output structure only. It does not establish accuracy against a real oracle.

## Current Validation Status
The solver passed syntax, interface, and basic mock-callback execution checks. Testing against a real oracle simulator, confusion-matrix evaluation, accuracy-versus-budget measurements, and noise robustness remain outstanding.

## Files
- solver.py — solver implementation
- test_solver.py — basic mock-callback test
- requirements.txt — Python dependencies
- logs/ — test records and benchmark data
- reports/ — technical report and AI-use disclosure
