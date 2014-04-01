from optimisation_algorithm import *

class SteepestDescent(OptimisationAlgorithm):
    """
        Implements the steepest descent method. 
     """
    def __init__(self, tol=1e-4, options={}, hooks={}, **args):
        '''
        Initialises the steepest descent algorithm. 
        
        Valid options are:

         * tol: Functional reduction stopping tolerance: |j - j_prev| < tol. Default: 1e-4.
         * options: A dictionary containing additional options for the steepest descent algorithm. Valid options are:
            - maxiter: Maximum number of iterations before the algorithm terminates. Default: 200. 
            - disp: dis/enable outputs to screen during the optimisation. Default: True
            - gtol: Gradient norm stopping tolerance: ||grad j|| < gtol.
            - line_search: defines the line search algorithm to use. Default: strong_wolfe
            - line_search_options: additional options for the line search algorithm. The specific options read the help 
              for the line search algorithm.
            - an optional callback method which is called after every optimisation iteration.
         * hooks: A dictionariy containing user-defined "hook" functions that are called at certain events during the optimisation.
            - before_iteration: Is called after before each iteration.
            - after_iteration: Is called after each each iteration.
          '''

        # Set the default options values
        self.tol = tol
        self.gtol = options.get("gtol", 1e-4)
        self.maxiter = options.get("maxiter", 200)
        self.disp = options.get("disp", True)
        self.line_search = options.get("line_search", "strong_wolfe")
        self.line_search_options = options.get("line_search_options", {})
        self.ls = get_line_search_method(self.line_search, self.line_search_options)
        self.callback = options.get("callback", None)
        self.hooks = hooks

    def __str__(self):
        s = "Steepest descent method.\n"
        s += "-"*30 + "\n"
        s += "Line search:\t\t %s\n" % self.line_search 
        s += "Maximum iterations:\t %i\n" % self.maxiter 
        return s

    def solve(self, problem, m):
        '''
            Arguments:
             * problem: The optimisation problem.

            Return value:
              * solution: The solution to the optimisation problem 
         '''

        j = None 
        j_prev = None

        obj = problem.obj
        m_prev = m.__class__(m)

        # Start the optimisation loop
        it = 0
        while True:

            # Evaluate the functional at the current iterate
            if j == None:
                j = obj(m)
            grad = obj.gradient(m) 


            if self.hooks.has_key("before_iteration"):
                self.hooks["before_iteration"](j, grad)

            if self.disp:
                print "Iteration %i\tJ = %s\t|dJ| = %s" % (it, j, grad.norm("L2"))

            # Check for convergence                                                                        # Reason:
            if not ((self.gtol    == None or grad.norm("L2") > self.gtol) and                              # ||\nabla j|| < gtol
                    (self.tol     == None or j == None or j_prev == None or abs(j-j_prev)) > self.tol and  # \Delta j < tol
                    (self.maxiter == None or it < self.maxiter)):                                          # maximum iteration reached
                break

            # Compute slope at current point
            djs = -grad.inner(grad)

            if djs >= 0:
                raise RuntimeError, "Negative gradient is not a descent direction. Is your gradient correct?" 

            # Define the real-valued reduced function in the s-direction 
            def phi(alpha):
                tmpm = m_prev.__class__(m_prev)
                tmpm.axpy(-alpha, grad)

                return obj(tmpm)

            def phi_dphi(alpha):
                tmpm = m_prev.__class__(m_prev)
                tmpm.axpy(-alpha, grad)

                p = phi(alpha) 
                djs = -obj.derivative(tmpm)(grad)
                return p, djs

            alpha = self.ls.search(phi, phi_dphi)

            # update m and j_new
            m = m_prev.__class__(m_prev)
            m.axpy(-alpha, grad)
            j_new = phi(alpha)

            # Update the current iterate
            m_prev = m.__class__(m)
            j_prev = j
            j = j_new
            it += 1

            if self.callback is not None:
                self.callback(j, -grad, m)

            if self.hooks.has_key("after_iteration"):
                self.hooks["after_iteration"](j, grad)

        # Print the reason for convergence
        if self.disp:
            n = grad.norm("L2")
            if self.maxiter != None and iter <= self.maxiter:
                print "\nMaximum number of iterations reached.\n"
            elif self.gtol != None and n <= self.gtol: 
                print "\nTolerance reached: |dJ| < gtol in %i iterations.\n" % it
            elif self.tol != None and j_prev != None and abs(j-j_prev) <= self.tol:
                print "\nTolerance reached: |delta j| < tol in %i interations.\n" % it

        sol = Solution({"Optimizer": m,
                        "Number of iterations": it})
        return sol
