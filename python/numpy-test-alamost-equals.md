## Test dataframes equality of a for desired precision

Use [numpy.testing.assert_array_almost_equal()](https://numpy.org/doc/stable/reference/generated/numpy.testing.assert_array_almost_equal.html) to test the results of a computation against a pre-computed dataframe, with a desired precision.

```python
np.testing.assert_array_almost_equal([1.0,2.333,np.nan],
                                     [1.0,2.33301,np.nan])
```
