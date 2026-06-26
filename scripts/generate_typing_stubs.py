# This file is used to automatically generate typing stubs for the Java classes used in the project

import stubgenj

from stream.java_api import ensure_jvm

ensure_jvm()

# Import all packages for which typing stubs are needed
import dk.brics

stubgenj.generateJavaStubs(
    [dk.brics], useStubsSuffix=False, outputDir="typings", jpypeJPackageStubs=False
)
