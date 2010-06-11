import itertools

import numpy

def squeeze(vectors,var,**kwargs):
    std=abs(var)**0.5
    small=approx(std,**kwargs) & numpy.isfinite(std)
    
    if small.size:
        var = var[~small]
        vectors = vectors[~small,:]
    
    return var,vectors

def mag2(vectors):
    return numpy.real_if_close(
        numpy.sum(
            numpy.array(vectors)*numpy.array(vectors.conjugate()),
            axis = vectors.ndim-1
    )) 

def sign(self):
    """
    improved sign function:
        returns a similar array of unit length (possibly complex) numbers pointing in the same 
        direction as the input 
    """
    return numpy.divide(
        self,
        abs(self),
    )
 
def unit(self):
    return numpy.array(self)/mag2(self,squeeze=False)**0.5

def ascomplex(self):
    """
    return an array pointing to the same data, but interpreting it as a 
    different type
    """
    shape=self.shape
    duplicate=self
    duplicate.dtype=complex
    duplicate.shape=shape[:-1]
    return duplicate

def diagstack(arrays):
    """
    stack matrixes diagonally
    1d arrays are interpreted as 1xN
    it's like numpy.diag but works with matrixes

    output is two dimensional

    type matches first input, if it is a numpy array or matrix, 
    otherwise this returns a numpy array
    """
    #make a nested matrix, with the inputs on the diagonal, and the numpy.zeros
    #function everywhere else
    result=numpy.where(
        numpy.eye(len(arrays)),
        numpy.diag(numpy.array(arrays,dtype=object)),
        numpy.zeros,
    )
    
    return autostack(result)

def autostack(rows,default=0):
    """
    simplify matrix stacking
    vertically stack the results of horizontally stacking each row in rows, 
    with no need to explicitly declare the size of and callables
    
    >>> autostack([ 
    ...     [numpy.eye(3),numpy.zeros],
    ...     [  numpy.ones,          1],
    ... ])
    matrix([[ 1.,  0.,  0.,  0.],
            [ 0.,  1.,  0.,  0.],
            [ 0.,  0.,  1.,  0.],
            [ 1.,  1.,  1.,  1.]])
    
    Callables are called with a shape tuple as the only argument. 
    The 'default' parameter controls the size when a row of column contains 
    only callables, 

    >>> autostack([
    ...     [[1,2,3]],
    ...     [numpy.ones]
    ... ],default=0)
    matrix([[ 1.,  2.,  3.]])
    
    >>> autostack([
    ...     [[1,2,3]],
    ...     [numpy.ones]
    ... ],default=4)
    matrix([[ 1.,  2.,  3.],
            [ 1.,  1.,  1.],
            [ 1.,  1.,  1.],
            [ 1.,  1.,  1.],
            [ 1.,  1.,  1.]])

    >>> autostack([
    ...     [                       [1,2,3],   1],
    ...     [lambda shape:numpy.eye(*shape),[[1]
    ...                                    , [1]]]
    ... ])
    matrix([[ 1.,  2.,  3.,  1.],
            [ 1.,  0.,  0.,  1.],
            [ 0.,  1.,  0.,  1.]])
    """
    
    #convert the data items into an object array 
    data = numpy.array( 
        [   #it's strange that I have to chain on these zeros to have the 
            #to get numpy to unpack 1 element lists into the array 
            list(itertools.chain([0],row)) 
            for row in rows
        ],
        dtype = object
    )[:,1:]
    
    #store the shape ofthe data
    shape=data.shape

    #and the type of the first numpy thing
    types=[type(item) for item in data.flatten() if isinstance(item,numpy.ndarray)]
    
    #make a matrix of the callable status of each item
    calls=numpy.array([callable(item) for item in data.flatten()]).reshape(shape)

    #convert all the non-callable elements to matrixes
    data=numpy.array([
        item if call else numpy.matrix(item) 
        for call,item in zip(calls.flat,data.flat)
    ],dtype=object).reshape(shape)

    #if anything is callable
    if calls.any():
        #make an array of shapes
        shapes = numpy.array([
            (-numpy.inf,-numpy.inf) if call else item.shape 
            for call,item in zip(calls.flatten(),data.flatten())
        ]).reshape(shape+(2,))
        
        #the first sheet is the heights
        heights=shapes[...,0]
        #the second is the widths
        widths=shapes[...,1]
        
        #the heights should be the same along each row
        #except for the -inf's that  we have for the callables
        maxheight=heights.max(1)
        maxwidth=widths.max(0)
        
        #replace the -inf's with the default value
        maxheight[maxheight==-numpy.inf] = default
        maxwidth[maxwidth==-numpy.inf] = default
        
        for (down,right) in numpy.argwhere(calls):
            #call the callable with (height,width) as the only argument
            #and drop it into the data slot,
            data[down,right] = numpy.matrix(data[down,right](
                (maxheight[down],maxwidth[right])
            ))
        
    #do the stacking    
    return numpy.vstack([
        numpy.hstack(row) 
        for row in data
    ])


def paralell(*items):
    """
    resistors in paralell, and thanks to 
    duck typing and operator overloading, this happens 
    to be exactly what we need for kalman sensor fusion. 
    """
    inverted=[item**(-1) for item in items]
    return sum(inverted[1:],inverted[0])**(-1)

def approx(a,other = None,atol=1e-5,rtol=1e-8):
    """
    like numpy.allclose, and numpy.real_if_close but returns a bool array
    
    a     -is the array of interest
    other -if None     delta=abs(a)
           if callable delta=abs(a-other(a.shape))
           else        delta=abs(a-other)
        
    returns True where delta<atol or delta/max(delta)<rtol 
    """
    if other is None :
        delta = numpy.abs(a)
    else:
        if callable(other):
            other=other(a.shape)
        delta = numpy.abs(a-other)

    
    MAX = numpy.max(delta) if delta.size else 0
    #if the largest element is less than the absolute tolerence
    #then everythng is approx=
    if MAX<atol:
        return numpy.ones(delta.shape,dtype=bool)
    
    return (delta<atol) | (delta/MAX<rtol) if MAX else (delta<atol)

def dots(*args):
    """
    like numpy.dot but takes any number or arguments
    """
    assert len(args)>1
    return reduce(numpy.dot,args)

def sortrows(data,column=0):
    return data[numpy.argsort(data[:,column].flatten()),:] if data.size else data

def rotation2d(angle):
    return numpy.array([
        [ numpy.cos(angle),numpy.sin(angle)],
        [-numpy.sin(angle),numpy.cos(angle)],
    ])


