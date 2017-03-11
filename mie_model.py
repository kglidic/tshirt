import numpy as np
import miescatter
import pdb
import matplotlib.pyplot as plt
import es_gen
import yaml

coeff = yaml.load(open('parameters/mie_params/simplePoly.yaml'))


def polyExtinct(wavel,rad=1.0,type=r'Simple n=(1.67-0.006j)'):
    """
    Extinction function using a high order polynomial fit
    """
    normWave = wavel/rad
    Carr = coeff[type]['coefficients']
    return np.polyval(Carr,normWave)

def polyExtinctMatrix(wavel,rad=1.0,type=r'Simple n=(1.67-0.006j)'):
    """
    Extinction function using a high order polynomial fit
    """
    normWave = wavel/rad
    Carr = np.array(coeff[type]['coefficients'])
    nOrder = len(Carr)
    #nX = normWave.size[0]
    
    x2D = np.tile(normWave,(nOrder,1)).transpose()
    xPowers = x2D**np.arange(nOrder)
    
    return np.dot(xPowers,np.flip(Carr,0))

def extinct(wavel,rad=1.0,n=complex(1.825,-1e-4),logNorm=False,
            npoint=128,pdfThreshold=0.001,s=0.5):
    """
    Calculates the Mie extinction cross section Q_ext as a function of wavelength
    
    Arguments
    ------------------
    rad: float
        The radius of the particle
    wavel: float,arr
        The array of wavelengths to evaluate
    """
    sz = 2. * np.pi * rad/np.array(wavel)
    
    if logNorm == True:
        ## Generate an array of points along the distribution
        ## Size multiplier
        nwav = sz.size
        ## Size to evaluate lognormal weights
        ## Make a linear space from threshold to threshold in the PDF
        lowEval, highEval = invLognorm(s,rad,pdfThreshold)
        sizeEval = np.linspace(lowEval,highEval,npoint)
        weights = lognorm(sizeEval,s,1.)
        sumWeights = np.sum(weights) * (sizeEval[1] - sizeEval[0])
        if (sumWeights < 0.8) | (sumWeights > 1.001):
            print('Warning, PDF weights not properly sampling PDF')
        weights = weights / sumWeights
        ## Arrange the array into 2D for multiplication of the grids
        sizeMult = (np.tile(sizeEval,(nwav,1))).transpose()
        sizeArr = np.tile(sz,(npoint,1))
        
        eval2D = sizeMult * sizeArr
        finalEval = eval2D.ravel() ## Evaluate a 1D array
        pdb.set_trace()
    else:
        finalEval = np.array(sz)
        
    ## Make all points with sz > 100. the same as 100
    ## Otherwise the miescatter code quits without any warning or diagnostics
    highp = finalEval > 100.
    finalEval[highp] = 100.
    
    qext,qsca,qabs,qbk,qpr,alb,g = miescatter.calcscatt(n,finalEval,n=finalEval.size)
    
    if logNorm == True:
        ## Now sum by the weights
        qext2D = np.reshape(qext,(npoint,nwav))
        finalQext = np.dot(weights,qext2D) * (sizeEval[1] - sizeEval[0])
    else:
        finalQext = qext
        
    return finalQext

def invLognorm(s,med,pdfThreshold):
    """ 
    Calculates the X values for a Log-normal distribution evaluated at specific PDF values
    
    Arguments
    ------------------
    s: float
        The sigma (scale value) of the log-normal distribution
    med: float
        The median particle size
    pdfThreshold: float
        The PDF threshold at which to find the x values
    """
    mu = np.log(med)
    sqrtPart = np.sqrt(-2. * s**2 * np.log(s * np.sqrt(2. * np.pi) * pdfThreshold))
    lowEval = np.exp(mu - sqrtPart)
    highEval = np.exp(mu + sqrtPart)
    
    return lowEval, highEval

def lognorm(x,s,med):
    """
    Calculates a log-normal size distribution
    
    Arguments
    ------------------
    x: arr
        The input particle size
    s: float
        The sigma value
    med: float
        The median particle size
    """
    mu = np.log(med)
    y = 1. / (s*np.sqrt(2.*np.pi)) * np.exp(-0.5*(np.log(x-mu)/s)**2)
    return y

def showLognorm():
    """ Shows example log-normal distributions"""
    rad = 0.5
    #sArray = [0.4,0.5,0.6]
    sArray = [1.0,0.5,0.25]
    plt.close('all')
    fig, ax = plt.subplots()
    for oneS in sArray:
        lowEval, highEval = invLognorm(oneS,rad,0.005)
        x = np.linspace(lowEval,highEval,1024)
        y = lognorm(x,oneS,rad)
        ax.plot(x,y,label='s='+str(oneS))
    ax.set_xlim(0,3)
    fig.show()

def compareTest():
    """
    Compares the Single Particle and Log-normal distributions
    """
    x = np.linspace(0.2,15,1024)
    rad = 1.0
    nInd=complex(1.825,-1e-4)
    ysingle = extinct(x,rad=rad,logNorm=False,n=nInd)
    plt.loglog(x,ysingle,label='Single Particle')
    npointA = [32,64,128,256]
    for npoint in npointA:
        ymulti = extinct(x,rad=rad,logNorm=True,npoint=npoint,n=nInd)
        plt.plot(x,ymulti,label='Log Normal N='+str(npoint)+',[0.2,5]')
    yWider = extinct(x,rad=rad,logNorm=True,npoint=256,n=nInd,
                     lowMult=0.1,highMult=10.)
    plt.plot(x,yWider,label='Log normal N=256,[0.1,10]')
    plt.legend(loc='best')
    plt.show()
    
def getPoly(pord=15):
    """
    Fits a polynomial to a Mie extinction curve
    """
    x = np.linspace(0.2,15,1024)
    rad = 1.0
    nInd = complex(1.67,-0.006)
    y = extinct(x,rad=rad,logNorm=True,npoint=1024,n=nInd)
    polyFit = es_gen.robust_poly(x,y,pord,sigreject=100.)
    plt.loglog(x,y,label='Log-Normal Q$_{ext}$')
    plt.plot(x,np.polyval(polyFit,x),label='Polynomial Fit')
    plt.legend(loc='best')
    
    fitDict = {'Simple n='+str(nInd):{'coefficients':polyFit.tolist()}}
    with open('parameters/mie_params/simplePoly.yaml','w') as outFile:
        yaml.dump(fitDict,outFile,default_flow_style=False)
    plt.show()
    