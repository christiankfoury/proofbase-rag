"""Same durable accounting; one explicitly declared 91-call diagnostic allowance."""
from decimal import Decimal
from scripts.quality_completion_durable import Ledger as PreviousLedger, write_json_atomic
from scripts.quality_eval_transport_v12 import BudgetStop


class Ledger(PreviousLedger):
    def begin_stage(self, name, maximum_calls, upper_bound):
        self.reload()
        if self.data['stage'] is not None:
            raise BudgetStop('A stage is already reserved')
        limit = 91 if name == 'v18-diagnostic' else 75
        if type(maximum_calls) is not int or not 0 < maximum_calls <= limit:
            raise BudgetStop('Invalid predeclared stage call count')
        if not upper_bound.is_finite() or upper_bound <= 0:
            raise BudgetStop('Invalid stage estimate')
        self.data['stage'] = {'name':name,'start_calls':len(self.data['calls']),
                              'maximum_calls':maximum_calls,'upper_bound_usd':str(upper_bound),
                              'start_spent_usd':str(self.spent)}
        write_json_atomic(self.path,self.data)
