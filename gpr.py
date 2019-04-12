import numpy as np
import os, sys
from classes.shared_functions import *
from classes.database_class import *
from statistics import mean, stdev
from matplotlib import pyplot as plt
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel, Product, ExpSineSquared

# # Generate Test Data
# rng = np.random.RandomState(0)
# X = rng.uniform(0, 5, 20)[:, np.newaxis]
# y = 0.5 * np.sin(3 * X[:, 0]) + rng.normal(0, 0.5, X.shape[0])
#
# # First run
# plt.figure(0)
# kernel = 1.0 * RBF(length_scale=100.0, length_scale_bounds=(1e-2, 1e3)) \
#     + WhiteKernel(noise_level=1, noise_level_bounds=(1e-10, 1e+1))
# gp = GaussianProcessRegressor(kernel=kernel,
#                               alpha=0.0).fit(X, y)
# X_ = np.linspace(0, 5, 100)
# y_mean, y_cov = gp.predict(X_[:, np.newaxis], return_cov=True)
# plt.plot(X_, y_mean, 'k', lw=3, zorder=9)
# plt.fill_between(X_, y_mean - np.sqrt(np.diag(y_cov)),
#                  y_mean + np.sqrt(np.diag(y_cov)),
#                  alpha=0.5, color='k')
# plt.plot(X_, 0.5*np.sin(3*X_), 'r', lw=3, zorder=9)
# plt.scatter(X[:, 0], y, c='r', s=50, zorder=10, edgecolors=(0, 0, 0))
# plt.title("Squared Exponential Kernel")
# plt.tight_layout()
# print("\nSquared-Exponential, Sample Data")
# print("Initial Kernel: {}\nOptimum Kernel: {}\n Log-Marginal-Likelihood: {}".format(\
#     kernel, gp.kernel_, gp.log_marginal_likelihood(gp.kernel_.theta)))
#
# # Second run
# plt.figure(1)
# kernel = 1.0 * RBF(length_scale=1.0, length_scale_bounds=(1e-2, 1e3)) \
#     + WhiteKernel(noise_level=1e-5, noise_level_bounds=(1e-10, 1e+1))
# gp = GaussianProcessRegressor(kernel=kernel,
#                               alpha=0.0).fit(X, y)
# X_ = np.linspace(0, 5, 100)
# y_mean, y_cov = gp.predict(X_[:, np.newaxis], return_cov=True)
# plt.plot(X_, y_mean, 'k', lw=3, zorder=9)
# plt.fill_between(X_, y_mean - np.sqrt(np.diag(y_cov)),
#                  y_mean + np.sqrt(np.diag(y_cov)),
#                  alpha=0.5, color='k')
# plt.plot(X_, 0.5*np.sin(3*X_), 'r', lw=3, zorder=9)
# plt.scatter(X[:, 0], y, c='r', s=50, zorder=10, edgecolors=(0, 0, 0))
# plt.title("Periodic Kernel")
# plt.tight_layout()
# print("\nPeriodic, Sample Data")
# print("Initial Kernel: {}\nOptimum Kernel: {}\n Log-Marginal-Likelihood: {}".format(\
#     kernel, gp.kernel_, gp.log_marginal_likelihood(gp.kernel_.theta)))
#
# # Custom run
# plt.figure(2)
# k1 = 1.0 * RBF(length_scale=1.0, length_scale_bounds=(1e-2, 1e3))
# k2 = ExpSineSquared(length_scale=1.0, periodicity=1.0, \
#     length_scale_bounds=(1e-05, 100000.0), periodicity_bounds=(1e-05, 100000.0))
# k3 = WhiteKernel(noise_level=1e-5, noise_level_bounds=(1e-10, 1e+1))
# kernel = Product(k1,k2) + k3
# gp = GaussianProcessRegressor(kernel=kernel,
#                               alpha=0.0).fit(X, y)
# X_ = np.linspace(0, 5, 100)
# y_mean, y_cov = gp.predict(X_[:, np.newaxis], return_cov=True)
# plt.plot(X_, y_mean, 'k', lw=3, zorder=9)
# plt.fill_between(X_, y_mean - np.sqrt(np.diag(y_cov)),
#                  y_mean + np.sqrt(np.diag(y_cov)),
#                  alpha=0.5, color='k')
# plt.plot(X_, 0.5*np.sin(3*X_), 'r', lw=3, zorder=9)
# plt.scatter(X[:, 0], y, c='r', s=50, zorder=10, edgecolors=(0, 0, 0))
# plt.title("Quasi-Periodic Kernel")
# plt.tight_layout()
# print("\nQuasi-Periodic, Sample Data")
# print("Initial Kernel: {}\nOptimum Kernel: {}\n Log-Marginal-Likelihood: {}".format(\
#     kernel, gp.kernel_, gp.log_marginal_likelihood(gp.kernel_.theta)))

# REAL DATA

# Getting data from database
dirname = os.path.dirname(os.path.realpath(__file__))
set_folder_paths(dirname)
gc = database(data(db_name), 'gymchecker', gc_params)
entries = gc.get_all()
# Filter entries for only open hours
data = []
for e in sorted(entries,key=lambda x: x[0]):
    dt = datetime.datetime.fromtimestamp(e[0])
    d = dt.weekday()
    t = 2 * (dt.hour + dt.minute/60)
    oh = open_hours[d]
    if oh[0] <= t <= oh[1]:
        data.append( (e[0],e[4]) )

subset_length = 300
test_length = 25

ppp = subset_length - test_length
print(ppp)
subset = data[-1*subset_length:]
start = subset[0][0]
dx, dy = [(x[0] - start)/1000 for x in subset], [y[1] for y in subset]
train_x, train_y = dx[:ppp], dy[:ppp]
test_x, test_y = dx[ppp:],dy[ppp:]

# Plot data subset
plt.figure(3)
plt.plot(dx,dy)
plt.title("Plotted Data")

k1 = 1.0 * RBF(length_scale=1.0, length_scale_bounds=(1e-2, 1e3))
k2 = ExpSineSquared(length_scale=1.0, periodicity=605, \
    length_scale_bounds=(1e-05, 100000.0), periodicity_bounds=(1e-05, 1000.0))
k3 = WhiteKernel(noise_level=1e-5, noise_level_bounds=(1e-10, 1e+1))
kernel = Product(k1,k2) + k3

tests = []
while len(test_x) > 0:
    sys.stdout.write("\r{}   ".format(len(test_x)))
    sys.stdout.flush()
    # Predict point
    # Append (point, prediction)
    # Add to x points
    X = np.asarray(train_x)[:,np.newaxis]
    Y = np.asarray(train_y)[:,np.newaxis]
    px, py = test_x.pop(0), test_y.pop(0)
    gp = GaussianProcessRegressor(kernel=kernel,
                                  alpha=0.0).fit(X, Y)
    sample = np.asarray([px])[:,np.newaxis]
    pred = gp.predict(sample)[0][0]
    tests.append(abs(py-pred))
    train_x.append(px)
    train_y.append(py)

print("\r")
print(tests)
print(mean(tests))
print(stdev(tests))


# Transform to numpy data types
# X_ = np.linspace(0, 600, 1000)
# y_mean, y_cov = gp.predict(X_[:, np.newaxis], return_cov=True)
# print(X_)
# plt.plot(X_, y_mean, 'k', lw=3, zorder=9)
# plt.fill_between(X_, y_mean - np.sqrt(np.diag(y_cov)),
#                  y_mean + np.sqrt(np.diag(y_cov)),
#                  alpha=0.5, color='k')
# plt.scatter(X2[:, 0], y2, c='r', s=50, zorder=10, edgecolors=(0, 0, 0))
# plt.title("Squared Exponential Kernel")
# plt.tight_layout()
# print("\nReal Data")
# print("Initial Kernel: {}\nOptimum Kernel: {}\nLog-Marginal-Likelihood: {}".format(\
#     kernel, gp.kernel_, gp.log_marginal_likelihood(gp.kernel_.theta)))
#
# plt.show()
