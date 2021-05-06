class Node:
    def __init__(self, actions):
        # actions = [''.join(action) for action in actions]
        self.actions = actions

        self.regret_sum = {action: 0 for action in actions}
        self.curr_strategy = {action: 0 for action in actions}
        self.strategy_sum = {action: 0 for action in actions}

    def strategy(self, weight=1):
        actions = self.actions
        strat = {action: max(value, 0) for action, value in
                 self.regret_sum.items()}

        norm_sum = sum([strat[key] for key in strat])

        if norm_sum > 0:
            strat = {key: strat[key] / norm_sum for key in actions}
        else:
            num_valid = len(actions)
            strat = {key: 1 / num_valid for key, value in strat.items()}

        self.strategy_sum = {key: value + strat[key] * weight for key, value
                             in self.strategy_sum.items()}

        return strat

    def avg_strategy(self):
        avg_strategy = {action: 0 for action in self.actions}
        norm_sum = sum([value for key, value in self.strategy_sum.items()])

        if norm_sum > 0:
            avg_strategy = dict((key, self.strategy_sum[key] / norm_sum) for
                                key in self.strategy_sum.keys())
        else:
            avg_strategy = dict((key, 1 / len(self.actions))
                                for key in self.strategy_sum.keys())

        self.curr_strategy = avg_strategy

        return avg_strategy

    def __repr__(self):
        return 'strategy_sum: {strategy_sum}\n regret: {regret_sum}\n'.format(strategy_sum=self.strategy_sum,
                                                                              regret_sum=self.regret_sum)


class MNode(Node):
    def __init__(self, actions):
        super().__init__(actions)

    def strategy(self):
        actions = self.actions
        strat = {action: max(value, 0) for action, value in
                 self.regret_sum.items()}

        norm_sum = sum([strat[key] for key in strat])

        if norm_sum > 0:
            strat = {key: strat[key] / norm_sum for key in actions}
        else:
            num_valid = len(actions)
            strat = {key: 1 / num_valid for key, value in strat.items()}

        return strat