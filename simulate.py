from dynamicMatchingMarket.Market import (
    ArrivalDistribution,
    DepartureDistribution,
    MatchFunction,
    GreedyMarket, 
    PatientMarket
)

m=1000
d=5
T=100

market = GreedyMarket(
    m,
    d,
    departureDistribution=DepartureDistribution.CONSTANT,
    departureDistributionParameters={"value":1},
    arrivalDistribution=ArrivalDistribution.POISSON,
    matchFunction=MatchFunction.RANDOM
)

print(market.run(T))

market = PatientMarket(
    m,
    d,
    departureDistribution=DepartureDistribution.CONSTANT,
    departureDistributionParameters={"value":1},
    arrivalDistribution=ArrivalDistribution.POISSON,
    matchFunction=MatchFunction.RANDOM
)

print(market.run(T))