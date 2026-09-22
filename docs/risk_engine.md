# Multi-Dimensional Risk Engine Framework

## Overview
The Risk Engine evaluates 5 normalized risk components (0 to 100 scale) and synthesizes a transparent **Composite Risk Index**.

## Risk Component Formulations

1. **Stockout Risk Score ($R_{\text{stockout}}$)**:
   $$R_{\text{stockout}} = \max\left(0, \min\left(100, \frac{ROP - I_{\text{current}}}{ROP} \times 100\right)\right)$$
   Evaluates imminent stock depletion when current inventory falls below $ROP$.

2. **Overstock Risk Score ($R_{\text{overstock}}$)**:
   $$R_{\text{overstock}} = \max\left(0, \min\left(100, \frac{I_{\text{current}} - (ROP + EOQ)}{I_{\text{current}}} \times 100\right)\right)$$
   Measures capital tie-up risk when inventory exceeds the maximum desired buffer ($ROP + EOQ$).

3. **Demand Volatility Risk Score ($R_{\text{volatility}}$)**:
   $$R_{\text{volatility}} = \min(100, \text{CV} \times 50)$$
   Evaluates demand instability using Coefficient of Variation ($\text{CV} = \sigma / \mu$).

4. **Forecast Uncertainty Risk Score ($R_{\text{uncertainty}}$)**:
   $$R_{\text{uncertainty}} = \min\left(100, \frac{y_{p90} - y_{p10}}{y_{p50}} \times 40\right)$$
   Evaluates machine learning prediction interval width relative to expected median demand.

5. **Lead-Time Risk Score ($R_{\text{leadtime}}$)**:
   $$R_{\text{leadtime}} = \min(100, \sigma_L \times 20)$$
   Evaluates supply chain supplier delivery variance.

---

## Composite Risk Weightings

$$\text{Composite Risk} = 0.30 R_{\text{stockout}} + 0.25 R_{\text{overstock}} + 0.20 R_{\text{uncertainty}} + 0.15 R_{\text{volatility}} + 0.10 R_{\text{leadtime}}$$

### Classification Scale
- **CRITICAL HIGH**: Score $\ge 70.0$
- **MODERATE**: Score $40.0 \le \text{Score} < 70.0$
- **LOW**: Score $< 40.0$
