#!/usr/bin/env python3
"""
Smart learning management script
"""
import sys
import time
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    parser = argparse.ArgumentParser(description="Manage smart continuous learning")
    parser.add_argument("command", choices=["start", "stop", "status", "check", 
                                          "rebuild", "export", "test", "init"],
                       help="Command to execute")
    parser.add_argument("--question", type=str, help="Question to test")
    parser.add_argument("--interval", type=int, default=300,
                       help="Check interval in seconds")
    
    args = parser.parse_args()
    
    # Import from app.core
    from app.core.smart_continuous_learner import get_smart_learner, initialize_smart_learning
    import logging
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    learner = get_smart_learner()
    
    if args.command == "init":
        print("🔄 Initializing smart learning...")
        initialize_smart_learning()
        status = learner.get_status()
        print(f"✅ Initialized with {status['direct_answers']} answers")
        print(f"📁 PDFs directory: {status['pdfs_directory']}")
    
    elif args.command == "start":
        print("🚀 Starting smart continuous learning...")
        
        # Initialize if needed
        if not learner.direct_answers:
            initialize_smart_learning()
        
        # Set check interval if provided
        if args.interval:
            learner.check_interval = args.interval
        
        learner.start()
        print("✅ Smart learning started")
        print(f"📁 Monitoring: {learner.pdfs_dir}")
        print(f"📚 Current answers: {len(learner.direct_answers)}")
        print(f"⏱️ Check interval: {learner.check_interval} seconds")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping...")
            learner.stop()
    
    elif args.command == "stop":
        print("🛑 Stopping smart learning...")
        learner.stop()
        print("✅ Smart learning stopped")
    
    elif args.command == "status":
        status = learner.get_status()
        print("📊 Smart Learning Status")
        print("=" * 50)
        print(f"📈 Running: {status['running']}")
        print(f"📁 PDFs Directory: {status['pdfs_directory']}")
        print(f"📋 Tracked Files: {status['tracked_files']}")
        print(f"💬 Direct Answers: {status['direct_answers']}")
        print(f"📖 Definitions: {status['definitions']}")
        print(f"🔑 Keywords Mapped: {status['keywords_mapped']}")
        print(f"⏱️ Check Interval: {status['check_interval']} seconds")
        print(f"⏰ Last Check: {status['stats']['last_check'] or 'Never'}")
        print(f"📝 Last Updated: {status['stats']['last_updated'] or 'Never'}")
        print(f"❌ Errors: {status['stats']['errors']}")
        print("\n📝 Sample Questions:")
        for q in status.get('sample_questions', [])[:5]:
            print(f"  • {q}")
    
    elif args.command == "check":
        print("🔍 Forcing immediate check...")
        learner.force_check()
        print("✅ Check completed")
    
    elif args.command == "rebuild":
        print("🔄 Rebuilding answer database from all PDFs...")
        confirm = input("This will rebuild from scratch. Continue? (y/N): ")
        if confirm.lower() == 'y':
            # Clear and rebuild
            learner.direct_answers.clear()
            learner.definitions.clear()
            learner.keywords.clear()
            learner.file_hashes.clear()
            
            pdf_files = list(learner.pdfs_dir.glob("*.pdf"))
            print(f"Found {len(pdf_files)} PDFs")
            
            for pdf_path in pdf_files:
                print(f"Processing {pdf_path.name}...")
                try:
                    learner._process_pdf(pdf_path)
                except Exception as e:
                    print(f"❌ Error processing {pdf_path.name}: {e}")
            
            learner._build_common_answers()
            print(f"✅ Rebuilt. Total answers: {len(learner.direct_answers)}")
        else:
            print("❌ Rebuild cancelled")
    
    elif args.command == "export":
        print("📤 Exporting to strict_rag format...")
        success = learner.export_to_strict_rag_format()
        if success:
            print("✅ Export successful")
            print(f"📝 Answers exported: {len(learner.direct_answers)}")
            print(f"💾 File: {learner.data_dir}/strict_rag_auto.py")
        else:
            print("❌ Export failed")
    
    elif args.command == "test":
        if not args.question:
            print("❌ Please provide a question with --question")
            return
        
        print(f"🧪 Testing: {args.question}")
        answer = learner.get_direct_answer(args.question)
        
        if answer:
            print(f"✅ Found answer ({len(answer)} chars):")
            print("-" * 50)
            print(answer[:500] + ("..." if len(answer) > 500 else ""))
            print("-" * 50)
        else:
            print("❌ No direct answer found")
            print("💡 Try variations or check the PDF content")
    
    else:
        print(f"❌ Unknown command: {args.command}")
        print("Available commands: start, stop, status, check, rebuild, export, test, init")

if __name__ == "__main__":
    main()
