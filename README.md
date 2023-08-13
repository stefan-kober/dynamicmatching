# Dynamic Matching Markets - Simulation

Repository to simulate dynamic matching markets with random arrival and departure processes.
Supplementary code to *Superiority of Instantaneous Decisions in Thin Dynamic Matching Markets* [1].

## Usage

Example usage is demonstrated in the file ```simulate.py```.
We provide two different ```Market``` classes, depending on the employed matching algorithms, namely the ```GreedyMarket``` and the ```PatientMarket```.
Further parameters are ```m```, i.e., the arrival rate, ```d```, the expected number of compatible partners arriving in 1 timeunit, the matching function, and the arrival and departure distributions.
When running a specified market, this always happens for a specified amount of time (```T```).

An example call of a ```GreedyMarket``` looks like this (see also ```simulate.py```)

```
market = GreedyMarket(
    m = 1000,
    d = 5,
    departureDistribution = DepartureDistribution.CONSTANT,
    departureDistributionParameters = {"value":1},
    arrivalDistribution = ArrivalDistribution.POISSON,
    matchFunction = MatchFunction.RANDOM
)

print(market.run(100))
```

Evaluations can only be performed on markets that have been run.

[1]: Johannes Bäumler, Martin Bullinger, Stefan Kober, and Donghao Zhu. 2023. Superiority of Instantaneous Decisions in Thin Dynamic Matching Markets. In Proceedings of the 24th ACM Conference on Economics and Computation (EC '23). Association for Computing Machinery, New York, NY, USA, 390. https://doi.org/10.1145/3580507.3597660