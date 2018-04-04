# To build and run the documentation

cd ..; sphinx-apidoc -o docs poseidon -F; pushd docs; make html; make man; popd
