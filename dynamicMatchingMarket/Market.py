from enum import IntEnum
import networkx as nx
import numpy as np
from sortedcontainers import SortedDict

from .Agent import Agent

class ArrivalDistribution(IntEnum):
    POISSON = 1
    CONSTANT = 2

class DepartureDistribution(IntEnum):
    CONSTANT = 1
    EXPONENTIAL = 2
    UNIFORM = 3

class MatchFunction(IntEnum):
    RANDOM = 1
    FIRSTEXIT = 2
    LASTEXIT = 3

class Market():
    class Status(IntEnum):
        CREATED = 1
        RUNNING = 2
        FINISHED = 3
        ERROR = 4
        
    def __init__(self,m,d,departureDistribution=DepartureDistribution.CONSTANT,departureDistributionParameters={},arrivalDistribution=ArrivalDistribution.POISSON,matchFunction=MatchFunction.RANDOM,seed=None):
        self.m = m
        self.d = d
        self.p = self.d/self.m
        self.scale = 1/self.m
        self.rng = np.random.default_rng(seed)

        self.departureDistribution = departureDistribution
        if self.departureDistribution==DepartureDistribution.CONSTANT:
            if "value" in departureDistributionParameters:
                self.dd_value = departureDistributionParameters["value"]
            else:
                self.dd_value = 1
            self._departureDistributionFunction = self._constantDepartureDistributionFunction
        elif self.departureDistribution==DepartureDistribution.EXPONENTIAL:
            if "scale" in departureDistributionParameters:
                self.dd_scale = departureDistributionParameters["scale"]
            else:
                self.dd_scale = 1
            self._departureDistributionFunction = self._exponentialDepartureDistributionFunction
        elif self.departureDistribution==DepartureDistribution.UNIFORM:
            if "lb" in departureDistributionParameters:
                self.dd_lb = departureDistributionParameters["lb"]
            else: 
                self.dd_lb = 0
            if "ub" in departureDistributionParameters:
                self.dd_ub = departureDistributionParameters["ub"]
            else:
                self.dd_ub = 0
            self._departureDistributionFunction = self._uniformDepartureDistributionFunction
        else: 
            raise AssertionError(f"departure distribution {departureDistribution} not known!")

        self.arrivalDistribution = arrivalDistribution
        if arrivalDistribution==ArrivalDistribution.POISSON:
            self._getNextEntry = self._nextEntryPoisson
        elif arrivalDistribution==ArrivalDistribution.CONSTANT:
            self._getNextEntry = self._nextEntryConstant
        else: 
            raise AssertionError(f"arrival distribution {arrivalDistribution} not known!")

        self.matchFunction = matchFunction
        if matchFunction==MatchFunction.RANDOM:
            self._getMatch = self._randomMatch
        elif matchFunction==MatchFunction.FIRSTEXIT:
            self._getMatch = self._firstExitMatch
        elif matchFunction==MatchFunction.LASTEXIT:
            self._getMatch = self._lastExitMatch
        else: 
            raise AssertionError(f"match function {matchFunction} not known!")

        self._checkRunning = self._checkRaiseRunning
        
        self.agents = {}
        self.agent_log = {}
        self.graph = nx.empty_graph()
        self.nextExits = SortedDict()

        self.num_agents = 0
        self.num_successfullyMatchedAgents = 0
        self.num_failedAgents = 0

        self.time = 0
        self.event_log = []
        self.status = self.Status.CREATED
        return

    def run(self,time):
        if not self.status == self.Status.CREATED:
            raise AssertionError("please recreate")
        self.totalTime = time

        if self.arrivalDistribution == ArrivalDistribution.POISSON:
            self.exp_vector = self.rng.exponential(self.scale, 2*self.totalTime*self.m)

        self.status = self.Status.RUNNING
        self._checkRunning = lambda: None
        self._announceNextAgent()
        while self.time<self.totalTime:
            self._step()
        self.loss = self.num_failedAgents/self.num_agents
        self._checkRunning = self._checkRaiseRunning
        self.status = self.Status.FINISHED
        return self.loss

    def _match(self,agent):
        self._checkRunning()
        neighbors = np.array(list(self.graph.neighbors(agent)))
        if not neighbors.size == 0:
            return self._getMatch(neighbors)
        return False

    def _createAgent(self,name,time):
        self._checkRunning()
        self.num_agents+=1
        neighbors=[]

        agent_vec = list(self.agents.keys())
        random_vec = self.rng.random(len(agent_vec))
        neighbor_indices = np.where(random_vec<=self.p)
        neighbors = [agent_vec[i] for i in neighbor_indices[0]]

        self.agents[name]=Agent(name,self._departureDistributionFunction(),time)
        self.agent_log[name]=self.agents[name]
        self.graph.add_node(name)
        for neighbor in neighbors:
            self.graph.add_edge(name,neighbor)
            
        self.nextExits[time+self.agents[name].sojourn] = name
        return name

    def _removeAgent(self,agent):
        self._checkRunning()
        del self.nextExits[self.agents[agent].exitTime]
        del self.agents[agent]
        self.graph.remove_node(agent)
        return

    def _announceNextAgent(self):
        self._checkRunning()
        self.nextEntry = self._getNextEntry()

    def _nextEntryPoisson(self):
        self._checkRunning()
        try:
            _val, self.exp_vector = self.exp_vector[0],self.exp_vector[1:]
        except IndexError:
            self.exp_vector = self.rng.exponential(self.scale, self.totalTime*self.m)
            return self._nextEntryPoisson()
        return _val

    def _nextEntryConstant(self):
        self._checkRunning()
        return self.scale

    def _constantDepartureDistributionFunction(self):
        self._checkRunning()
        return self.dd_value

    def _exponentialDepartureDistributionFunction(self):
        self._checkRunning()
        return self.rng.exponential(scale=self.dd_scale)

    def _uniformDepartureDistributionFunction(self):
        self._checkRunning()
        return self.dd_lb+(self.dd_ub-self.dd_lb)*self.rng.random()

    def _randomMatch(self,match_list):
        self._checkRunning()
        return match_list[self.rng.integers(match_list.size)]

    def _firstExitMatch(self,match_list):
        self._checkRunning()
        return sorted(match_list, key=lambda x:self.agents[x].exitTime)[0]

    def _lastExitMatch(self,match_list):
        self._checkRunning()
        return sorted(match_list, reverse=True, key=lambda x:self.agents[x].exitTime)[0]

    def _checkRaiseRunning(self):
        if not self.status == self.Status.RUNNING:
            raise AssertionError("only available during simulation run")

    def _step(self):
        raise NotImplementedError()

class PatientMarket(Market):
    def _step(self):
        self._checkRunning()
        for key,agent in self.nextExits.items():
            if key<self.time+self.nextEntry:
                if agent in self.agents:
                    match = self._match(agent)
                    if match is not False:
                        self.event_log.append(("match",key,agent,match))
                        self._removeAgent(agent)
                        self._removeAgent(match)
                        self.num_successfullyMatchedAgents+=2
                    else:
                        self.event_log.append(("leave",key,agent,-1))
                        self._removeAgent(agent)
                        self.num_failedAgents+=1
            else:
                break

        self.time+=self.nextEntry
        if self.time<self.totalTime:
            agent = self._createAgent(self.num_agents,self.time)
            self.event_log.append(("join",self.time,agent,-1))
            self._announceNextAgent()
        return
        
class GreedyMarket(Market):
    def _step(self):
        self._checkRunning()
        for key,agent in self.nextExits.items():
            if key<self.time+self.nextEntry:
                self.event_log.append(("leave",key,agent,-1))
                self._removeAgent(agent)
                self.num_failedAgents+=1
            else:
                break
            
        self.time+=self.nextEntry
        if self.time<self.totalTime:
            agent = self._createAgent(self.num_agents,self.time)
            self.event_log.append(("join",self.time,agent,-1))
            match = self._match(agent)
            if match is not False:
                self.event_log.append(("match",self.time,agent,match))
                self._removeAgent(agent)
                self._removeAgent(match)
                self.num_successfullyMatchedAgents+=2
            self._announceNextAgent()
        return