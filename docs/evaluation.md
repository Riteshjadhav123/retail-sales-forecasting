# Model Evaluation Methodology & Metrics

## Point Forecast Metrics

1. **Mean Absolute Error (MAE)**:
   $$\text{MAE} = \frac{1}{n} \sum_{i=1}^{n} |y_i - \hat{y}_i|$$
   Measures average absolute magnitude of errors in sales currency ($).

2. **Root Mean Squared Error (RMSE)**:
   $$\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2}$$
   Penalizes large outlier forecast errors heavily.

3. **Weighted Absolute Percentage Error (WAPE)**:
   $$\text{WAPE} = \frac{\sum_{i=1}^{n} |y_i - \hat{y}_i|}{\sum_{i=1}^{n} |y_i|}$$
   Scale-independent demand accuracy metric robust against zero division.

4. **Coefficient of Determination ($R^2$)**:
   $$R^2 = 1 - \frac{\sum (y_i - \hat{y}_i)^2}{\sum (y_i - \bar{y})^2}$$
   Proportion of variance explained by the model.

---

## Probabilistic Interval Metrics

1. **Empirical Coverage Percentage (PICR)**:
   $$\text{Coverage} = \frac{1}{n} \sum_{i=1}^{n} \mathbb{I}(y_i \in [\hat{y}_{i,p10}, \hat{y}_{i,p90}]) \times 100\%$$

2. **Mean Interval Width (MPIW)**:
   $$\text{MPIW} = \frac{1}{n} \sum_{i=1}^{n} (\hat{y}_{i,p90} - \hat{y}_{i,p10})$$

3. **Calibration Error**:
   $$\text{Calibration Error} = |\text{Empirical Coverage} - \text{Target Coverage}|$$
