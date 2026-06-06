## Prerequisite knowledge:
	For our specific use cases I researched different common cloud compute providers and their costs. I compared this with less utilized ones that offer better prices, and what we can use. Throughout this report I kept in mind that starting out we are looking for cost effective solutions before building our user base where we will most likely need to find a larger and more expensive solution/provider.


---

## What we are looking for:
	Specifically with the Flux2 dev, Flux2 Klein, RMBG-1.4, and Gemma3 (8B) models we require lots of VRAM, high memory bandwidth, and parallel processing for the image generation models. Due to the amount of users we have currently, it is ideal if we can utilize infrastructure that only charges us when the GPU's are being utilized (we can move to a "always on" provider later). The draw back of this would be each time a user requests something on our end, a cold start would cause the boot time for the AI models to be close to possibly 30 seconds. However this would reduce costs by an extremely significant amount.


---

## Example Comparison:
	This comparison is made with the highest end AI specific GPU's in order to see the price difference, however GPU's such as consumer grade RTX 5090's can be utilized in order to reduce costs by half or a quarter of what is seen.

| **Category**                | **Large Server Providers (AWS, GCP, Azure)**         | **AI Clouds (RunPod, Lambda Labs)**                            |
| --------------------------- | ---------------------------------------------------- | -------------------------------------------------------------- |
| **Pricing (H100/A100)**     | $4.00 - $8.00+ / hour                                | $1.50 - $2.50 / hour                                           |
| **Egress Fees (Bandwidth)** | High (Charges per GB out)                            | Zero or Negligible                                             |
| **Setup Speed**             | Complex (Have full control of the system)            | Instant (Containerized Pods, Developer-first)                  |
| **Ecosystem**               | Massive (Databases, Queues, Security out-of-the-box) | Focused purely on raw compute, some load balancing and queuing |

---

## Benefits and Drawbacks:

### **Large Server Providers:**
- **Pros:** Extremely reliable, available globally, Infinite scalability.
- **Cons:** Extreme cost on GPU hourly rates, locked in with the vendor, hidden costs (especially with images and larger files).
### **AI Clouds:**
- **Pros:** Extremely cost efficient. Access to consumer GPUs which are which are perfect for our specific models and even cheaper. Fast, Docker-native deployments and customization.
- **Cons:** We must handle our own load balancing and database connections (they provide mostly just compute). Occasional shortages due to high traffic which may increase compute time (rare).

---

## Scalability Strategy:
	Since we are starting out with a low number of users, it doesn't make sense to use an "always on" dedicated server right now. Here is the plan I put together for how we handle this issue:

- **Right Now:** We start with Serverless GPU endpoints on a provider like RunPod. This lets us pay strictly for the compute time we use. When nobody is using the AI models, our cost is $0. The main trade-off is the cold start time I mentioned earlier (up to 30 seconds for the first request), but that is fine for an early rollout to preserve our budget, because the alternative cost is too large.
- **When our user base grows:** Once we have a steady stream of users, we move to Dedicated Pods. We can rent cost effective consumer GPUs (like the RTX 5090 or 4090) for a flat hourly rate. Because the models will stay loaded in VRAM, our users will get instant response times.

---

## My Recommendation:
	I recommend we go with RunPod (or a similar AI cloud like Lambda Labs) for our initial use. It fits our current baseline by letting us scale to zero, and it keeps our compute costs roughly 70% cheaper (or greater savings depending on the GPU's we decide to utilize) than AWS. We can always migrate to a bigger provider later if we need strict enterprise compliance, but right now this is the best option.

---

## Links:

### AI Clouds (Recommended for Cost & Speed):

- **RunPod:** [runpod.io](https://www.runpod.io/)
	
- **Lambda Labs:** [lambdalabs.com](https://lambdalabs.com/)

### The Big Three Providers:

- **Amazon Web Services (AWS):** [aws.amazon.com](https://aws.amazon.com/)
    
    - *Equivalent AI Service (SageMaker):_ [aws.amazon.com/sagemaker](https://aws.amazon.com/sagemaker/)*
        
- **Google Cloud Platform (GCP):** [cloud.google.com](https://cloud.google.com/)
    
    - _Equivalent AI Service (Vertex AI):_ [cloud.google.com/vertex-ai](https://cloud.google.com/vertex-ai)
        
- **Microsoft Azure:** [azure.microsoft.com](https://azure.microsoft.com/)
    
    - _Equivalent AI Service (Azure AI):_ [azure.microsoft.com/en-us/solutions/ai/](https://azure.microsoft.com/en-us/solutions/ai/)