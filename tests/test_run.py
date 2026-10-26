import sys
import traceback
sys.path.insert(0, '.')
try:
    from main import main
    main()
except Exception as e:
    traceback.print_exc()
    input("Press enter to exit...")