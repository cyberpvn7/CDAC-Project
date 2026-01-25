#!/usr/bin/env python3
"""
SecGuys Master Orchestrator
Unified pipeline: setup → scan → normalize → ingest → analyze → semantic enrichment
"""

import subprocess
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Add src and setup directories to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "setup"))

from config import CONFIG
import init_db
from normalize_scans import normalize_scans
import validator


# ===========================
# LOGGING SETUP
# ===========================

def setup_logging():
    """Initialize logging"""
    log_dir = Path(CONFIG["logging"]["dir"])
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"secguys_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=CONFIG["logging"]["level"],
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


logger = setup_logging()


# ===========================
# PHASE 1: ENVIRONMENT SETUP
# ===========================

def phase_setup(skip=False):
    """Initialize database and ensure all tools are available"""
    logger.info("=" * 60)
    logger.info("PHASE 1: Environment Setup")
    logger.info("=" * 60)
    
    if skip:
        logger.info("⏭️  Skipping setup (--skip-setup)")
        return True
    
    try:
        # Validate tools
        logger.info("Checking required tools...")
        validator.validate_required_tools()
        logger.info("✅ All tools available")
        
        # Validate Python modules
        logger.info("Checking Python modules...")
        validator.validate_python_modules()
        logger.info("✅ All modules available")
        
        # Initialize database
        logger.info("Initializing database...")
        if not init_db.init_database():
            raise RuntimeError("Database initialization failed")
        
        # Validate database
        logger.info("Validating database schema...")
        validator.validate_database_initialized()
        logger.info("✅ Database validated")
        
        logger.info("✅ Environment setup completed")
        return True
        
    except validator.ValidationError as e:
        logger.error(str(e))
        return False
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        return False


# ===========================
# PHASE 2: VULNERABILITY SCANNING
# ===========================

def phase_scan(targets: List[str], skip=False):
    """Execute all security scanners"""
    logger.info("=" * 60)
    logger.info("PHASE 2: Vulnerability Scanning")
    logger.info("=" * 60)
    
    if skip:
        logger.info("⏭️  Skipping scan (--skip-scan)")
        return True
    
    try:
        # Validate prerequisites
        logger.info("Validating scan prerequisites...")
        validator.validate_required_tools()
        logger.info("✅ Validated")
        
        scan_results_dir = Path(CONFIG["scanner"]["results_dir"])
        scan_results_dir.mkdir(exist_ok=True)
        
        for target in targets:
            logger.info(f"\n🎯 Scanning target: {target}")
            
            # Build scanner.sh command
            cmd = [
                "bash",
                "tools/scanner.sh"
            ]
            
            # Pass target via stdin to avoid interactive prompt
            result = subprocess.run(
                cmd,
                input=target,
                capture_output=True,
                text=True,
                timeout=CONFIG["scanner"]["timeout"]
            )
            
            if result.returncode != 0:
                logger.warning(f"⚠️  Scanner exited with code {result.returncode}")
                logger.debug(f"stdout: {result.stdout}")
                logger.debug(f"stderr: {result.stderr}")
            else:
                logger.info(f"✅ Scan completed for {target}")
        
        # Validate scan produced results
        logger.info("Validating scan results...")
        validator.validate_scan_results_exist()
        logger.info("✅ Scan results validated")
        
        return True
        
    except validator.ValidationError as e:
        logger.error(str(e))
        return False
    except subprocess.TimeoutExpired:
        logger.error(f"❌ Scan timeout after {CONFIG['scanner']['timeout']}s")
        return False
    except Exception as e:
        logger.error(f"❌ Scan failed: {e}")
        return False


# ===========================
# PHASE 3: NORMALIZATION
# ===========================

def phase_normalize(targets: List[str]):
    """Normalize scanner outputs into unified final.json"""
    logger.info("=" * 60)
    logger.info("PHASE 3: Normalization")
    logger.info("=" * 60)
    
    try:
        for target in targets:
            logger.info(f"Normalizing results for {target}...")
            
            final_data = normalize_scans(target)
            
            output_path = Path(CONFIG["scanner"]["results_dir"]) / "final.json"
            import json
            with open(output_path, "w") as f:
                json.dump(final_data, f, indent=2)
            
            logger.info(f"✅ Normalized: {output_path}")
        
        # Validate normalized output
        logger.info("Validating normalized output...")
        validator.validate_final_json()
        logger.info("✅ Validation passed")
        
        return True
        
    except validator.ValidationError as e:
        logger.error(str(e))
        return False
    except Exception as e:
        logger.error(f"❌ Normalization failed: {e}")
        return False


# ===========================
# PHASE 4: DATABASE INGESTION
# ===========================

def phase_ingest():
    """Ingest normalized findings into database"""
    logger.info("=" * 60)
    logger.info("PHASE 4: Database Ingestion")
    logger.info("=" * 60)
    
    try:
        # Validate prerequisites
        logger.info("Validating ingestion prerequisites...")
        validator.validate_database_initialized()
        validator.validate_final_json()
        logger.info("✅ Validated")
        
        logger.info("Running ingest_final.py...")
        
        result = subprocess.run(
            ["python3", "src/ingest_final.py"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        logger.info(result.stdout)
        
        if result.returncode != 0:
            logger.warning(f"⚠️  Ingestion exited with code {result.returncode}")
            if result.stderr:
                logger.debug(f"Error: {result.stderr}")
            return False
        
        # Validate data was ingested
        logger.info("Validating ingested data...")
        scan_id = validator.validate_completed_scan_exists()
        finding_count = validator.validate_findings_in_db(scan_id)
        logger.info(f"✅ {finding_count} findings ingested")
        
        return True
        
    except validator.ValidationError as e:
        logger.error(str(e))
        return False
    except subprocess.TimeoutExpired:
        logger.error("❌ Ingestion timeout")
        return False
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        return False


# ===========================
# PHASE 5: AI ANALYSIS
# ===========================

def phase_analyze():
    """Generate AI-powered security report"""
    logger.info("=" * 60)
    logger.info("PHASE 5: AI Analysis (Gemini)")
    logger.info("=" * 60)
    
    try:
        # Validate prerequisites
        logger.info("Validating AI analysis prerequisites...")
        validator.validate_analyze_prerequisites()
        logger.info("✅ Validated")
        
        logger.info("Running analyze_final.py...")
        
        result = subprocess.run(
            ["python3", "src/analyze_final.py"],
            capture_output=True,
            text=True,
            timeout=600,
            env={**subprocess.os.environ, "GEMINI_API_KEY": CONFIG["gemini"]["api_key"]}
        )
        
        logger.info(result.stdout)
        
        if result.returncode != 0:
            logger.warning(f"⚠️  Analysis exited with code {result.returncode}")
            if result.stderr:
                logger.debug(f"Error: {result.stderr}")
            return False
        
        logger.info("✅ AI report generated")
        return True
        
    except validator.ValidationError as e:
        logger.error(str(e))
        return False
    except subprocess.TimeoutExpired:
        logger.error("❌ Analysis timeout")
        return False
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        return False


# ===========================
# PHASE 6: SEMANTIC ENRICHMENT
# ===========================

def phase_semantic():
    """Enrich findings with semantic analysis and CVSS scoring"""
    logger.info("=" * 60)
    logger.info("PHASE 6: Semantic Enrichment")
    logger.info("=" * 60)
    
    if not CONFIG["semantic"]["enabled"]:
        logger.info("⏭️  Semantic analysis disabled")
        return True
    
    try:
        # Validate prerequisites
        logger.info("Validating semantic enrichment prerequisites...")
        validator.validate_semantic_prerequisites()
        logger.info("✅ Validated")
        
        logger.info("Running semantic_analyzer.py...")
        
        result = subprocess.run(
            ["python3", "src/transformer/semantic_analyzer.py"],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        logger.info(result.stdout)
        
        if result.returncode != 0:
            logger.warning(f"⚠️  Semantic analysis exited with code {result.returncode}")
            if result.stderr:
                logger.debug(f"Error: {result.stderr}")
            return False
        
        logger.info("✅ Semantic enrichment completed")
        return True
        
    except validator.ValidationError as e:
        logger.error(str(e))
        return False
    except subprocess.TimeoutExpired:
        logger.error("❌ Semantic analysis timeout")
        return False
    except Exception as e:
        logger.error(f"❌ Semantic analysis failed: {e}")
        return False


# ===========================
# VALIDATION & CHECKS
# ===========================

def validate_targets(targets: List[str]) -> bool:
    """Validate target list"""
    if not targets:
        logger.error("❌ No targets provided")
        return False
    
    for target in targets:
        if not target.strip():
            logger.error(f"❌ Invalid target: '{target}'")
            return False
    
    logger.info(f"✅ Validated {len(targets)} target(s)")
    return True


def check_prerequisites() -> bool:
    """Check if required tools are available"""
    try:
        logger.info("Checking required tools...")
        validator.validate_required_tools()
        logger.info("✅ All required tools available")
        return True
    except validator.ValidationError as e:
        logger.warning(str(e))
        return False


# ===========================
# MAIN ORCHESTRATION
# ===========================

def run_pipeline(
    targets: List[str],
    skip_setup: bool = False,
    skip_scan: bool = False,
    skip_analyze: bool = False,
    skip_semantic: bool = False,
    check_tools: bool = True
) -> bool:
    """Execute complete pipeline"""
    
    logger.info("")
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " " * 15 + "SECGUYS - Automated Scanning Pipeline" + " " * 4 + "║")
    logger.info("║" + " " * 20 + f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" + " " * 9 + "║")
    logger.info("╚" + "=" * 58 + "╝")
    logger.info("")
    
    # Validate inputs
    if not validate_targets(targets):
        return False
    
    if check_tools and not check_prerequisites():
        logger.warning("⚠️  Proceeding without tool check...")
    
    # Execute phases
    phases = [
        ("Setup", lambda: phase_setup(skip=skip_setup)),
        ("Scan", lambda: phase_scan(targets, skip=skip_scan)),
        ("Normalize", lambda: phase_normalize(targets)),
        ("Ingest", lambda: phase_ingest()),
        ("Analyze", lambda: phase_analyze() if not skip_analyze else True),
        ("Semantic", lambda: phase_semantic() if not skip_semantic else True),
    ]
    
    results = {}
    for phase_name, phase_func in phases:
        try:
            success = phase_func()
            results[phase_name] = success
            
            if not success:
                logger.error(f"❌ Pipeline halted at {phase_name}")
                break
        except Exception as e:
            logger.error(f"❌ Unexpected error in {phase_name}: {e}")
            results[phase_name] = False
            break
    
    # Summary
    logger.info("")
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " " * 20 + "PIPELINE SUMMARY" + " " * 20 + "║")
    logger.info("╠" + "=" * 58 + "╣")
    
    for phase_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"║ {phase_name:12} {status:40} ║")
    
    logger.info("╚" + "=" * 58 + "╝")
    
    overall_success = all(results.values())
    
    if overall_success:
        report_path = Path(CONFIG["scanner"]["results_dir"]).parent / "db_report.md"
        logger.info("")
        logger.info(f"📊 Final Report: {report_path}")
        logger.info(f"🗄️  Database: {CONFIG['database']['path']}")
    
    return overall_success


def main():
    parser = argparse.ArgumentParser(
        description="SecGuys - Unified Security Scanning & Analysis Pipeline"
    )
    
    parser.add_argument(
        "targets",
        nargs="+",
        help="Target IP/domain to scan (or file with list of targets)"
    )
    
    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="Skip environment setup"
    )
    
    parser.add_argument(
        "--skip-scan",
        action="store_true",
        help="Skip vulnerability scanning"
    )
    
    parser.add_argument(
        "--skip-analyze",
        action="store_true",
        help="Skip AI analysis (Gemini)"
    )
    
    parser.add_argument(
        "--skip-semantic",
        action="store_true",
        help="Skip semantic enrichment"
    )
    
    parser.add_argument(
        "--no-tool-check",
        action="store_true",
        help="Skip tool availability check"
    )
    
    args = parser.parse_args()
    
    # Handle file input (targets from file)
    targets = []
    for target_arg in args.targets:
        if Path(target_arg).is_file():
            with open(target_arg, "r") as f:
                targets.extend([line.strip() for line in f if line.strip()])
        else:
            targets.append(target_arg)
    
    # Run pipeline
    success = run_pipeline(
        targets=targets,
        skip_setup=args.skip_setup,
        skip_scan=args.skip_scan,
        skip_analyze=args.skip_analyze,
        skip_semantic=args.skip_semantic,
        check_tools=not args.no_tool_check
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
