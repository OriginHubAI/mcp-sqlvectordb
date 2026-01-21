# How to Generate the Dataset
The dataset generation method is derived from the dataset generation approach in https://github.com/OpenDCAI/Text2VectorSQL.

The detailed process is as follows:
1. Select the required dataset in the directory `Text2VectorSQL/Data_Synthesizer/pipeline/sqlite/train`.
2. Modify the configuration of the corresponding `Text2VectorSQL/Data_Synthesizer/pipeline/config.yaml` file.
3. Run `Text2VectorSQL/Data_Synthesizer/pipeline/general_pipeline.py` (you need to enable the corresponding operators in the file). This step is used to generate the SQLite database and the corresponding SQL statements.
4. Execute the script in `Text2VectorSQL/Data_Synthesizer/tools` to migrate the data from SQLite to the target database.
   Example command:
   ```bash
   python migrate_db_myscale.py --source /mnt/DataFlow/ydw/Text2VectorSQL/Data_Synthesizer/pipeline/sqlite/results/test/vector_databases --host xxxxxx --port 9000 --user default --password "xxxxx"
   ```
5. Execute the script to convert SQLite SQL statements to the corresponding target SQL statements. After execution, the required dataset file `candidate_sql.json` will be generated in the directory `/Data_Synthesizer/pipeline/myscale/results/test/` under the selected target database.
   Example command:
   ```bash
   python migrate_main_sql_only.py --workers 32 --myscale_password 'myscale#EDC' --datasets test
   ```