# Full-text read-through batch 08

## SCI-001411 — Estimation of Kenaf seedling canopy coverage in saline soil using semantic segmentation of UAV RGB images
attribution: CONFIRMED for model=SE-enhanced U-Net backbone=U-Net + Self-Attention (SE) channel mechanism dataset=Kenaf (Hibiscus cannabinus L.) seedlings in saline-alkali soil, UAV RGB

| claim key | claimed value | verdict | verbatim source quote |
|-----------|--------------|---------|----------------------|
| mIoU | 0.8599 | CONFIRMED | "the U-Net architecture was enhanced by incorporating a Self-Attention (SE) channel mechanism, further improving model performance to achieve an IoU of 85.99%" |
| F1 | 0.9244 | CONFIRMED | "an Dice of 92.44%" (binary segmentation Dice=F1) |
| Dice | 0.9244 | CONFIRMED | "an Dice of 92.44%" |
| PA | 0.9292 | CONFIRMED | Table 4: "SE-UNet AdamW 85.99 92.92 92.44 92.08 92.92" (Accuracy column) |
| device | None - offline experiments... | CONFIRMED | "All image processing and deep learning experiments were conducted on the same high-performance workstation. The hardware configuration includes a 13th-generation Intel Core i5-13490F processor..." |
| resolution_input | 512 | CONFIRMED | "Scale change: Images were scaled at six levels ... and uniformly cropped to 512×512 pixels" |
| framework | PyTorch 1.10 / CUDA 11.3 / Python 3.8 | CONFIRMED | "Python 3.8, CUDA 11.3, and PyTorch 1.10" |

## Batch summary
- SCI-001411: 7 confirmed, 0 mismatch, 0 not found, 0 low confidence
- Overall: 7 confirmed, 0 mismatch, 0 not found, 0 low confidence