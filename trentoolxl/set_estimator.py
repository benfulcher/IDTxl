import types
import random
import estimators_te

class Estimator_te(object):
    def __init__(self, estimator_name):
        try:
            estimator = getattr(estimators_te, estimator_name)
        except AttributeError:
            print('The requested TE estimator "' + estimator_name + '" was not found.')
        else:
            self.estimator_name = estimator_name
            self.addMethodAs(estimator, "estimate")
    @classmethod
    def removeMethod(cls, name):
        return delattr(cls, name)
    @classmethod
    def addMethodAs(cls, func, new_name=None):
        if new_name is None:
            new_name = fun.__name__
        return setattr(cls, new_name, types.MethodType(func, cls))
    def get_estimator(self):
        return self.estimator_name


if __name__ == "__main__":
    te_estimator = Estimator_te("jidt_kraskov")
    cmi_estimator = Estimator_cmi("jidt_kraskov")
    
    numObservations = 1000
    covariance=0.4
    source = [random.normalvariate(0,1) for r in range(numObservations)]
    target = [0] + [sum(pair) for pair in zip([covariance*y for y in source[0:numObservations-1]], \
                  [(1-covariance)*y for y in [random.normalvariate(0,1) for r in range(numObservations-1)]] ) ]
    conditional = [random.normalvariate(0,1) for r in range(numObservations)]
    knn = 4
    history_length = 1
    te = te_estimator.estimate(source, target, knn, history_length)
    print("Estimator is " + te_estimator.get_estimator())
    print("TE result: %.4f nats." % te)
