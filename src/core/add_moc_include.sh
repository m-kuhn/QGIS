git grep -l Q_OBJECT | while read -r f ; do
  base_name=$(basename ${f})
  base_name_cpp="${base_name%.h}.cpp"
  echo "#include <moc_${base_name%.h}.cpp>" >> "${f%.h}.cpp"
done
