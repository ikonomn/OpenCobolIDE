"""Windows one-file application and its editor/console workers."""
import runpy
import sys

if sys.argv[1:2] == ['--ocide-backend']:
    name = sys.argv[2]
    del sys.argv[1:3]
    modules = {'core-backend.exe': 'pyqode.core.backend.server',
               'cobol-backend.exe': 'pyqode.cobol.backend.server'}
    runpy.run_module(modules[name], run_name='__main__')
elif sys.argv[1:2] == ['--ocide-console']:
    from pyqode.core.tools.console import main
    del sys.argv[1]
    main()
else:
    from open_cobol_ide.main import main
    raise SystemExit(main())
