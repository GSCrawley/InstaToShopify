# Instagram to Etsy Print Shop Automation (auto_etsy)

## Project Overview

This project aims to create a fully automated pipeline to transform landscape photography from an Instagram account into a profitable Etsy print shop. It leverages print-on-demand services and incorporates intelligent content-based image discovery and search capabilities.

The core goal is to automate the process from image sourcing on Instagram, through content analysis and print optimization, to listing products on Etsy and managing the shop.

### MVP: Application for Personal Use (Initial Focus)

This project will initially be developed as an **MVP (Minimum Viable Product)** tailored for the primary user's personal use. While designed as a reusable application for a repeatable process, the immediate focus is on creating a functional tool for a single-user workflow. Future iterations may expand this to a more general, multi-user application.

The core workflow for this MVP will be:

* **Instagram Image Retrieval:** This is a two-stage process. First, the application will use a scraper (e.g., via Apify) to fetch recent posts from the user's specified Instagram profile(s). Second, for each scraped image, a Computer Vision (CV) model within our application will analyze its visual content. This CV analysis will filter the images based on a descriptive criterion provided by the user (e.g., to find all images visually containing a "sunset" or representing "New York City streets at dusk"), even if the original posts lack hashtags or detailed text descriptions.
* **Image Optimization:** Programmatically enhance and prepare the retrieved images to ensure they are print-worthy.
* **Cloud Storage:** Save the optimized images to the user's designated Google Cloud Storage bucket.
* **Print-on-Demand Integration:** Integrate with Printify to define product templates.
* **Etsy Listing Automation:** Automatically create and post these product templates as new listings on the user's Etsy shop, based on specified print types.
* **Notification:** Inform the user once new listings have been successfully posted.

The application will require the user to provide their credentials for Instagram (for the scraper), Google Cloud Storage, Printify, and Etsy.

## Comprehensive Guide

The detailed plan, technical specifications, and full project scope are documented in the [Comprehensive Guide: Instagram to Etsy Print Shop](./Instagram-to-Etsy-Print-Shop%20.md).

## Repository Structure

The organization of this repository is detailed in [repo-structure.md](./repo-structure.md).

## High-Level Project Phases

The project will be implemented in the following key phases:

1. **Phase 1: Instagram Image Acquisition & Content Analysis**
    * Authentication & Access (Instagram API/Scraping)
    * Image Discovery & Filtering (Criteria: aspect ratio, hashtags, quality, engagement, date)
    * Computer Vision Content Analysis (Object/scene detection, color analysis, composition, etc.)
2. **Phase 2: Image Processing & Print Optimization**
    * Image enhancement, resizing, color correction for print
    * Print quality assessment
3. **Phase 3: Print-on-Demand (PoD) Integration**
    * API integration with selected PoD services
    * Product creation and variant mapping
4. **Phase 4: Etsy Shop Management & Listing Automation**
    * Automated creation of Etsy listings
    * Dynamic population of metadata (titles, descriptions, tags) based on CV analysis
    * Management of pricing and shipping profiles
5. **Phase 5: Search & Discovery System**
    * Building a search index with CV-extracted features
    * Developing a user interface for content-based image search within the print shop
6. **Phase 6: Technical Architecture & Stack Implementation**
    * Setup of cloud storage (e.g., AWS S3, Google Cloud Storage)
    * Development of the Computer Vision processing pipeline
    * Configuration of monitoring (e.g., Prometheus, Grafana) and logging (e.g., ELK Stack)
    * Implementation of CI/CD pipelines (e.g., GitHub Actions)
7. **Phase 7: Success Metrics & KPIs**
    * Defining and tracking operational metrics (e.g., processing speed, CV accuracy)
    * Defining and tracking business metrics (e.g., conversion rates, revenue)
8. **Phase 8: Deployment**
    * Execution of the deployment checklist
    * Initial launch with a limited product set for validation and iteration

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Instagram account (for image acquisition)
- Printify account with API key
- Etsy shop connected to your Printify account
- (Optional) Google Cloud Storage account for image storage

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/auto_etsy.git
   cd auto_etsy
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv myenv
   # On Windows
   myenv\Scripts\activate
   # On macOS/Linux
   source myenv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with your credentials:
   ```
   # Instagram credentials
   INSTAGRAM_USERNAME=your_instagram_username
   INSTAGRAM_PASSWORD=your_instagram_password
   
   # Printify API credentials
   PRINTIFY_API_TOKEN=your_printify_api_token
   PRINTIFY_SHOP_ID=your_printify_shop_id
   
   # Google Cloud Storage (optional)
   USE_GCS=False
   GCS_BUCKET_NAME=your_gcs_bucket_name
   GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
   ```

### Usage

The application can be run using the `run.py` script at the project root:

```bash
# Run the full workflow (all phases)
python run.py --workflow full --instagram-user yourusername --limit 10

# Run only the image acquisition phase
python run.py --workflow acquisition --instagram-user yourusername --limit 5

# Run only the image processing phase (using existing images)
python run.py --workflow processing --input-dir data/raw --output-dir data/processed

# Run only the Print-on-Demand integration phase
python run.py --workflow pod

# Run with debug logging enabled
python run.py --workflow full --debug

# Get help on available options
python run.py --help
```

### Workflow Phases

1. **Acquisition**: Scrapes images from Instagram and filters them based on criteria
2. **Processing**: Optimizes images for printing (resizing, enhancing, etc.)
3. **POD Integration**: Uploads processed images to Printify and creates products
4. **Etsy Management**: Manages Etsy listings via Printify integration
5. **Discovery**: (Future) Implements search capabilities for finding optimal images

### Directory Structure

- `data/`: Stores images and metadata
  - `raw/`: Raw images downloaded from Instagram
  - `processed/`: Processed and optimized images
  - `metadata/`: Metadata about images and workflow runs
- `src/`: Source code
  - `phase1_acquisition/`: Instagram scraping and image filtering
  - `phase2_processing/`: Image processing and optimization
  - `phase3_pod_integration/`: Printify API integration
  - `phase4_etsy_management/`: Etsy shop management
  - `phase5_search_discovery/`: Search and discovery features
  - `utils/`: Utility functions and helpers
- `tests/`: Unit and integration tests
- `notebooks/`: Jupyter notebooks for exploration and analysis

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
