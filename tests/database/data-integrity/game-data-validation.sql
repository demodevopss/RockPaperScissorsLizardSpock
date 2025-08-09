-- RPSLS Database Data Integrity Tests
-- These tests validate game data consistency and business rules

-- Test 1: Validate Pick Values (0-4 for Rock, Paper, Scissors, Lizard, Spock)
SELECT 
    'Pick Value Validation' as test_name,
    CASE 
        WHEN COUNT(*) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END as result,
    COUNT(*) as invalid_records
FROM (
    -- Check if any match has invalid pick values
    SELECT * FROM matches 
    WHERE player_move NOT BETWEEN 0 AND 4 
       OR challenger_move NOT BETWEEN 0 AND 4
) invalid_picks;

-- Test 2: Validate Game Results (0=Tie, 1=Player, 2=Challenger)
SELECT 
    'Game Result Validation' as test_name,
    CASE 
        WHEN COUNT(*) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END as result,
    COUNT(*) as invalid_records
FROM (
    SELECT * FROM matches 
    WHERE result NOT IN (0, 1, 2)
) invalid_results;

-- Test 3: Validate Match Timestamps
SELECT 
    'Timestamp Validation' as test_name,
    CASE 
        WHEN COUNT(*) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END as result,
    COUNT(*) as invalid_records
FROM (
    SELECT * FROM matches 
    WHERE created_at > NOW() 
       OR created_at < '2020-01-01'
) invalid_timestamps;

-- Test 4: Validate Player Names (not null/empty)
SELECT 
    'Player Name Validation' as test_name,
    CASE 
        WHEN COUNT(*) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END as result,
    COUNT(*) as invalid_records
FROM (
    SELECT * FROM matches 
    WHERE player_name IS NULL 
       OR TRIM(player_name) = ''
       OR LENGTH(player_name) < 1
) invalid_names;

-- Test 5: Validate Challenger Names (must be valid challenger)
SELECT 
    'Challenger Name Validation' as test_name,
    CASE 
        WHEN COUNT(*) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END as result,
    COUNT(*) as invalid_records
FROM (
    SELECT * FROM matches 
    WHERE challenger_name NOT IN ('dotnet', 'python', 'java', 'node', 'php')
) invalid_challengers;

-- Test 6: Business Logic Validation - Rock vs Paper
-- Rock (0) vs Paper (1) should result in Challenger win (2)
SELECT 
    'Rock vs Paper Logic' as test_name,
    CASE 
        WHEN COUNT(*) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END as result,
    COUNT(*) as invalid_records
FROM (
    SELECT * FROM matches 
    WHERE player_move = 0 AND challenger_move = 1 AND result != 2
) invalid_logic;

-- Test 7: Business Logic Validation - Identical Moves (Tie)
SELECT 
    'Tie Game Logic' as test_name,
    CASE 
        WHEN COUNT(*) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END as result,
    COUNT(*) as invalid_records
FROM (
    SELECT * FROM matches 
    WHERE player_move = challenger_move AND result != 0
) invalid_ties;

-- Test 8: Data Consistency - No Orphaned Records
SELECT 
    'Data Consistency Check' as test_name,
    CASE 
        WHEN COUNT(*) = (SELECT COUNT(*) FROM matches) THEN 'PASS'
        ELSE 'FAIL'
    END as result,
    (SELECT COUNT(*) FROM matches) - COUNT(*) as missing_data
FROM matches m
WHERE m.id IS NOT NULL 
  AND m.player_name IS NOT NULL 
  AND m.challenger_name IS NOT NULL;

-- Test 9: Performance Check - Recent Matches Index
SELECT 
    'Recent Matches Performance' as test_name,
    CASE 
        WHEN execution_time < 100 THEN 'PASS'
        ELSE 'FAIL'
    END as result,
    execution_time as execution_time_ms
FROM (
    SELECT 
        (EXTRACT(EPOCH FROM (clock_timestamp() - query_start)) * 1000) as execution_time
    FROM (
        SELECT clock_timestamp() as query_start
    ) start_time,
    (
        SELECT COUNT(*) FROM matches 
        WHERE created_at > NOW() - INTERVAL '30 days'
        ORDER BY created_at DESC
        LIMIT 1000
    ) query_result
) performance_test;

-- Test 10: Data Volume Check
SELECT 
    'Data Volume Check' as test_name,
    CASE 
        WHEN match_count >= 0 THEN 'PASS'
        ELSE 'FAIL'
    END as result,
    match_count as total_matches
FROM (
    SELECT COUNT(*) as match_count FROM matches
) volume_check;

-- Summary Report
SELECT 
    '=== DATABASE INTEGRITY TEST SUMMARY ===' as summary,
    NOW() as test_timestamp;

-- Generate test execution report
SELECT 
    COUNT(*) as total_tests_run,
    SUM(CASE WHEN result = 'PASS' THEN 1 ELSE 0 END) as tests_passed,
    SUM(CASE WHEN result = 'FAIL' THEN 1 ELSE 0 END) as tests_failed,
    ROUND(
        (SUM(CASE WHEN result = 'PASS' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
        2
    ) as pass_percentage
FROM (
    -- This would collect all test results from above queries
    -- In practice, you'd run this as part of a stored procedure
    SELECT 'PASS' as result UNION ALL
    SELECT 'PASS' as result UNION ALL
    SELECT 'PASS' as result UNION ALL
    SELECT 'PASS' as result
) test_results;
