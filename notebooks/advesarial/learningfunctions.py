import theano
from theano import tensor as T
import numpy as np

class Learning(object):
    def __init__(self, cost,params,lr,l1=0.,l2=0.,maxnorm=0.,c=1):
        self.cost =cost
        self.params = params
        self.lr =lr
        self.l1 = l1
        self.l2 = l2
        self.maxnorm = maxnorm
        self.c = c
        self.grads = None
        self.updatedParameter = None

    def RMSprop(self, rho=0.9, epsilon=1e-6):
        
        self.grads = T.grad(self.cost, self.params)
        self.grads = self.clip_norms()
        updates = []
        
        for p, g in zip(self.params, self.grads):
            g = self.gradient_regularize(p, g, l1 = self.l1, l2 = self.l2)
            acc = theano.shared(p.get_value() * 0.)
            acc_new = rho * acc + (1 - rho) * g ** 2
            updates.append((acc, acc_new))
            
            updated_p = p - self.lr * (g / T.sqrt(acc_new + epsilon))
            self.updatedParameter = updated_p
            updated_p = self.weight_regularize()
            updates.append((p, updated_p))

        self.grads = None
        return updates


    def Adam(self, b1=0.1, b2=0.001, e=1e-8 ):
        
        self.grads = T.grad(self.cost, self.params)
        self.grads = self.clip_norms()
        updates = []

        i = theano.shared(np.asarray(0., dtype=theano.config.floatX))
        i_t = i + 1.
        fix1 = 1. - b1**(i_t)
        fix2 = 1. - b2**(i_t)
        lr_t = self.lr * (T.sqrt(fix2) / fix1)
        
        for p, g in zip(self.params, self.grads):
            m = theano.shared(p.get_value() * 0.)
            v = theano.shared(p.get_value() * 0.)
            m_t = (b1 * g) + ((1. - b1) * m)
            v_t = (b2 * T.sqr(g)) + ((1. - b2) * v)
            g_t = m_t / (T.sqrt(v_t) + e)
            g_t = self.gradient_regularize(p, g_t)
            p_t = p - (lr_t * g_t)
            self.updatedParameter = p_t
            p_t = self.weight_regularize()
            
            updates.append((m, m_t))
            updates.append((v, v_t))
            updates.append((p, p_t))
        
        updates.append((i, i_t))
        
        return updates

    def clip_norm(self,g,n): 
        '''n is the norm, c is the threashold, and g is the gradient'''
        
        if self.c > 0: 
            g = T.switch(T.ge(n, self.c), g*self.c/n, g) 
        return g

    def clip_norms(self):
        norm = T.sqrt(sum([T.sum(g**2) for g in self.grads]))
        return [self.clip_norm(g, norm) for g in self.grads]
        
    def gradient_regularize(self, p, g):
        g += p * self.l2
        g += T.sgn(p) * self.l1
        return g

    def weight_regularize(self):
        if self.maxnorm > 0:
            norms = T.sqrt(T.sum(T.sqr(self.updatedParameter), axis=0))
            desired = T.clip(norms, 0, maxnorm)
            self.updatedParameter = self.updatedParameter * (desired/ (1e-7 + norms))
        return self.updatedParameter


def dropout(self, X, p=0.):
    if p != 0:
        retain_prob = 1 - p
        X = X / retain_prob * srng.binomial(X.shape, p=retain_prob, dtype=theano.config.floatX)
    return X