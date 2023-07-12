# -*- coding: utf-8 -*-
"""Pantheon_matern_LBFGS.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1cGELEhcHJ0uC8WGRNdEsrZAeW4XXkDbE
"""

!pip install gpytorch

import torch
import gpytorch
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

data = pd.read_csv("/content/drive/MyDrive/Astrofinal/lcparam_full_long.txt", sep=" ", header=0)
redshift = torch.tensor(data['zcmb'].values, dtype=torch.float)
mag = torch.tensor(data['mb'].values, dtype=torch.float)
mag_err = torch.tensor(data['dmb'].values, dtype=torch.float)

# Definir el modelo de regresión gaussiana
class GaussianProcess(gpytorch.models.ExactGP):
    def __init__(self, train_x, train_y, likelihood):
        super(GaussianProcess, self).__init__(train_x, train_y, likelihood)
        self.mean_module = gpytorch.means.ConstantMean()
        self.covar_module = gpytorch.kernels.ScaleKernel(gpytorch.kernels.MaternKernel(nu=1.5, lengthscale=1))

    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)

# Definir la función de likelihood
likelihood = gpytorch.likelihoods.GaussianLikelihood()

# Inicializar el modelo
model = GaussianProcess(redshift, mag, likelihood)

# Entrenar el modelo
model.train()
likelihood.train()

# Definir el optimizador L-BFGS
optimizer = torch.optim.LBFGS(model.parameters(), lr=0.006)
mll = gpytorch.mlls.ExactMarginalLogLikelihood(likelihood, model)

# Definir la función de entrenamiento
def closure():
    optimizer.zero_grad()
    output = model(redshift)
    loss = -mll(output, mag)
    loss.backward()
    return loss

# Entrenar el modelo con L-BFGS durante 100 iteraciones
training_iterations = 100
loss_values = []
for i in range(training_iterations):
    loss = optimizer.step(closure)
    loss_values.append(loss.item())
    if i % 10 == 0:
        print(f"Iteration {i}: Loss = {loss_values[-1]}")
# Evaluar el modelo en un rango de valores de redshift
test_x = torch.linspace(redshift.min(), redshift.max(), 1000)
model.eval()
likelihood.eval()
with torch.no_grad():
    # Obtener la media y la varianza de la distribución gaussiana
    observed_pred = likelihood(model(test_x))
    mean = observed_pred.mean
    lower, upper = observed_pred.confidence_region() 
  # Graficar los resultados
plt.figure(figsize=(24, 14))
plt.errorbar(redshift.numpy(), mag.numpy(), yerr=mag_err.numpy(), fmt='o', markersize=3, alpha=0.5, label='Datos de supernovas')
plt.plot(test_x.numpy(), mean.numpy(), 'r', label='Predicción media')
plt.fill_between(test_x.numpy(), lower.numpy(), upper.numpy(), alpha=0.2, color='gray', label='Intervalo de confianza')
plt.xlabel('Redshift')
plt.ylabel('Magnitud aparente')
plt.legend()
plt.show()

# Plot the loss values over training iterations
plt.plot(loss_values)
plt.title('Loss over training iterations')
plt.xlabel('Training iteration')
plt.ylabel('Loss')
plt.show()

import numpy as np
import scipy.integrate as intg

def RHSquared_a_owacdm(a, w0, wa, Om):
    rhow = a**(-3*(1.0+w0+wa))*np.exp(-3*wa*(1-a))
    return (Om/a**3+(1.0-Om)*rhow)

def DistIntegrand_a(a, w0, wa, Om):
    return 1./np.sqrt(RHSquared_a_owacdm(a, w0, wa, Om))/a**2
    
def Da_z(z, w0=-1, wa=0.0, Om=0.23):
    r = intg.quad(DistIntegrand_a, 1./(1+z), 1, args=(w0, wa, Om))
    r = r[0]
    return r

def distance_modulus(z, w0=-1, wa=0.0, Om=0.23):
    return 5*np.log10(Da_z(z, w0, wa, Om)*(1+z))+24

zmodel = np.linspace(0.01, 2.3, 100)
flcdm = []
om = 0.27
for zzz in zmodel:
    flcdm.append(distance_modulus(zzz, w0=-1, wa=0, Om=om))
flcdm = np.array(flcdm)

# Graficar los resultados
plt.figure(figsize=(24, 14))
plt.errorbar(redshift.numpy(), mag.numpy(), yerr=mag_err.numpy(), fmt='o', markersize=3, alpha=0.5, label='Datos de supernovas')
plt.plot(test_x.numpy(), mean.numpy(), 'r', label='Predicción media')
plt.plot(zmodel, flcdm, label='$\Lambda CDM$', c='b')
plt.fill_between(test_x.numpy(), lower.numpy(), upper.numpy(), alpha=0.2, color='gray', label='Intervalo de confianza')
plt.xlabel('Redshift')
plt.ylabel('Magnitud aparente')
plt.legend()
plt.show()