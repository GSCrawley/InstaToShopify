# Enhanced Content Filtering Integration

## Overview

The Enhanced Content Filtering system has been successfully integrated into the main Instagram-to-Etsy workflow. This system provides intelligent content analysis, automatic video detection, quality scoring, and category-based filtering to ensure only the highest quality, most relevant images are selected for your print shop.

## Key Features

### 🎯 **Automatic Video Detection**
- Automatically detects and filters out video thumbnails
- Uses advanced computer vision techniques to identify video indicators
- Prevents low-quality video frames from entering your workflow

### 🏷️ **Intelligent Category Matching**
- Semantic understanding of image content using Google Vision API
- Pre-configured photography categories: landscape, sunset, water, nature, mountains, urban
- Configurable category weights and matching criteria

### 📊 **Multi-Factor Quality Scoring**
- **Technical Quality**: Resolution, aspect ratio, print suitability
- **Content Relevance**: Category matching scores
- **Print Optimization**: Suitability for wall art applications
- **Overall Score**: Weighted combination of all factors

### ⚙️ **Configurable Thresholds**
- Minimum quality scores
- Category matching requirements
- Overall acceptance criteria
- Fine-tune filtering to your specific needs

## Configuration

### Environment Variables (.env)

Add these optional settings to your `.env` file to customize the enhanced filtering:

```bash
# Enhanced Content Filtering Configuration
USE_ENHANCED_FILTERING=true
ENHANCED_CONTENT_CATEGORIES=landscape,sunset,water,nature,mountains,urban
MIN_QUALITY_SCORE=0.5
MIN_CATEGORY_SCORE=0.5
MIN_OVERALL_SCORE=0.6
MIN_PRINT_SUITABILITY=0.4
```

### Default Settings

If not specified in `.env`, the system uses these defaults:

- **Content Categories**: `['landscape', 'sunset', 'water', 'nature', 'mountains', 'urban']`
- **Min Quality Score**: `0.5`
- **Min Category Score**: `0.5`
- **Min Overall Score**: `0.6`
- **Min Print Suitability**: `0.4`
- **Enhanced Filtering**: `true` (enabled by default)

## Usage Examples

### 1. Basic Enhanced Filtering (Default Settings)

```bash
python src/main.py --workflow acquisition --enhanced-filter
```

### 2. Custom Content Categories

```bash
python src/main.py --workflow acquisition --enhanced-filter \
  --content-categories "landscape,sunset,nature"
```

### 3. Strict Quality Requirements

```bash
python src/main.py --workflow acquisition --enhanced-filter \
  --min-quality-score 0.7 \
  --min-category-score 0.6 \
  --min-overall-score 0.8
```

### 4. Relaxed Filtering for More Results

```bash
python src/main.py --workflow acquisition --enhanced-filter \
  --min-quality-score 0.3 \
  --min-category-score 0.3 \
  --min-overall-score 0.4
```

### 5. Disable Enhanced Filtering (Use Legacy System)

```bash
python src/main.py --workflow acquisition --content-filter \
  --filter-terms "sunset,mountains,nature"
```

## Command Line Arguments

### Enhanced Filtering Options

| Argument | Short | Type | Description |
|----------|-------|------|-------------|
| `--enhanced-filter` | `-ef` | flag | Enable enhanced content filtering (default: true) |
| `--content-categories` | `-cc` | string | Comma-separated content categories |
| `--min-quality-score` | `-mqs` | float | Minimum quality score (0.0-1.0) |
| `--min-category-score` | `-mcs` | float | Minimum category match score (0.0-1.0) |
| `--min-overall-score` | `-mos` | float | Minimum overall score (0.0-1.0) |

### Legacy Filtering Options (Still Available)

| Argument | Short | Type | Description |
|----------|-------|------|-------------|
| `--content-filter` | `-cf` | flag | Enable legacy content filtering |
| `--filter-terms` | `-ft` | string | Comma-separated content terms |

## How It Works

### 1. **Image Acquisition**
- Instagram posts are scraped using the Apify API
- Video posts are filtered out at the API level

### 2. **Enhanced Analysis Pipeline**
For each downloaded image:

1. **Video Thumbnail Detection**
   - Analyzes image for video indicators (play buttons, progress bars, etc.)
   - Rejects images identified as video thumbnails

2. **Google Vision API Analysis**
   - Extracts content labels and objects
   - Identifies dominant colors
   - Provides confidence scores

3. **Category Matching**
   - Matches detected content against configured categories
   - Uses semantic understanding for intelligent matching
   - Calculates weighted scores based on match quality

4. **Quality Assessment**
   - Evaluates technical image quality (resolution, aspect ratio)
   - Assesses print suitability for wall art
   - Considers file size and format

5. **Overall Scoring**
   - Combines all factors into a final score
   - Applies configurable thresholds
   - Makes accept/reject decision

### 3. **Results and Logging**
- Detailed logging of filtering decisions
- Analysis results stored in post metadata
- Summary statistics and reports

## Content Categories

### Pre-configured Categories

| Category | Primary Keywords | Use Case |
|----------|------------------|----------|
| **landscape** | landscape, mountain, valley, horizon, countryside, scenic, vista, panorama | Wide scenic views |
| **sunset** | sunset, sunrise, golden hour, dusk, dawn, twilight | Dramatic lighting |
| **water** | ocean, sea, lake, river, waterfall, stream, water, beach, coast | Water features |
| **nature** | nature, forest, tree, flower, plant, wildlife, animal | Natural subjects |
| **mountains** | mountain, peak, summit, alpine, ridge, cliff | Mountain landscapes |
| **urban** | city, urban, building, architecture, street, downtown | City scenes |

### Custom Categories

You can define custom categories by modifying the `ENHANCED_CONTENT_CATEGORIES` configuration or using the `--content-categories` command line argument.

## Scoring System

### Quality Score (0.0 - 1.0)
- **Resolution**: Based on pixel dimensions
- **Aspect Ratio**: Preference for printable ratios
- **File Size**: Larger files generally indicate better quality

### Category Score (0.0 - ∞)
- **Primary Keywords**: Full weight (1.0x)
- **Secondary Keywords**: Medium weight (0.6x)
- **Related Objects**: Lower weight (0.3x)
- **Category Weight**: Applied multiplier

### Print Suitability Score (0.0 - 1.0)
- **Print Resolution**: Minimum DPI requirements
- **Aspect Ratio**: Suitability for wall art
- **Content Relevance**: Based on category matches

### Overall Score (0.0 - ∞)
Weighted combination:
- Quality Score: 30%
- Print Suitability: 40%
- Category Score: 30% (normalized)

## Testing

### Run Integration Tests

```bash
python test_enhanced_integration.py
```

### Test Enhanced Filter on Existing Images

```bash
python test_enhanced_content_filter.py
```

### Test Specific Images

```bash
python -c "
from src.phase1_acquisition.enhanced_content_filter import EnhancedContentFilter
filter = EnhancedContentFilter()
meets_criteria, analysis = filter.meets_content_criteria('path/to/image.jpg')
print(f'Meets criteria: {meets_criteria}')
print(f'Overall score: {analysis.get(\"overall_score\", 0):.3f}')
"
```

## Troubleshooting

### Common Issues

1. **Google Vision API Not Available**
   - Ensure `GOOGLE_APPLICATION_CREDENTIALS` is set in `.env`
   - Verify credentials file exists and is valid
   - System will fall back to basic analysis if Vision API unavailable

2. **No Images Pass Filtering**
   - Lower the threshold scores
   - Check if content categories match your image types
   - Review logs for rejection reasons

3. **Too Many Images Pass Filtering**
   - Increase threshold scores
   - Add more specific content categories
   - Enable stricter quality requirements

### Debug Mode

Enable debug logging for detailed analysis:

```bash
python src/main.py --workflow acquisition --enhanced-filter --debug
```

### Log Analysis

Check the detailed logs in:
- `instagram_to_etsy.log` - Main workflow log
- `data/logs/scraping_results.log` - Scraping-specific results

## Performance Considerations

### Google Vision API Usage
- Each image analysis uses 1 API call
- Consider API quotas and costs for large batches
- System gracefully degrades if API unavailable

### Processing Speed
- Enhanced filtering adds ~1-2 seconds per image
- Parallel processing not currently implemented
- Consider batch size for large workflows

### Storage
- Analysis results stored in metadata files
- Approximately 2-5KB per image analysis
- Useful for debugging and optimization

## Migration from Legacy System

### Backward Compatibility
- Legacy content filtering still available
- Use `--content-filter` instead of `--enhanced-filter`
- Existing configurations continue to work

### Gradual Migration
1. Test enhanced filtering with existing images
2. Compare results with legacy system
3. Adjust thresholds as needed
4. Switch to enhanced filtering for new workflows

## Future Enhancements

### Planned Features
- Custom category definitions
- Machine learning model training
- Batch processing optimization
- Advanced print suitability analysis
- Integration with additional vision APIs

### Extensibility
The system is designed to be easily extended with:
- New content categories
- Additional quality metrics
- Custom scoring algorithms
- External API integrations

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Run the integration tests
3. Review the detailed logs
4. Adjust configuration settings as needed

The enhanced filtering system provides a powerful foundation for intelligent content curation, ensuring your print shop only features the highest quality, most relevant images.
