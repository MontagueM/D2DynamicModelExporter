import pkg_db


version = '3_0_0_4'

pkg_db.start_db_connection(version)

pkgs_to_check = pkg_db.get_all_tables()
for pkg in pkgs_to_check:
    model1_files = []
    model2_files = []
    # dyn models
    entries1_type = {x: y for x, y in pkg_db.get_entries_from_table(pkg, 'FileName, FileType') if y == 'Dynamic Model Header 1'}
    entries2_type = {x: y for x, y in pkg_db.get_entries_from_table(pkg, 'FileName, FileType') if y == 'Dynamic Model Header 2'}
    # entries_filetype = {x: y for x, y in pkg_db.get_entries_from_table(pkg, 'FileName, FileType') if y == '12 byte Stride Header'}
    for file in entries1_type.keys():
        model1_files.append(file)
    for file in entries2_type.keys():
        model2_files.append(file)
    print(f'{len(model1_files)} of dyn1; {len(model2_files)} of dyn2; in {pkg}')
    # print(f'{len(entries_filetype.keys())} models in {pkg}')
