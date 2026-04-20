#!/usr/bin/env python3
"""Pytest-based validation of prompt query examples with type hints and CLI support."""

import pytest
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

from opengenes_mcp.server import OpenGenesMCP, QueryResult


# Global server instance for tests
@pytest.fixture(scope="session")
def opengenes_server():
    """Create a single OpenGenesTools instance for all tests."""
    return OpenGenesMCP()


class TestPromptQueryValidation:
    """Test class for validating all query examples from the prompt."""

    def test_genes_increase_lifespan(self, opengenes_server) -> None:
        """Test basic query for genes that increase lifespan."""
        query = """
        SELECT HGNC, model_organism, effect_on_lifespan 
        FROM lifespan_change 
        WHERE effect_on_lifespan = 'increases lifespan'
        LIMIT 10
        """
        result: QueryResult = opengenes_server.db_query(query)
        
        assert result.count > 0, "Should find genes that increase lifespan"
        assert all('HGNC' in row for row in result.rows), "All rows should have HGNC"
        assert all(row['effect_on_lifespan'] == 'increases lifespan' for row in result.rows), \
            "All rows should have correct effect"

    def test_hallmarks_multi_value_search(self, opengenes_server) -> None:
        """Test LIKE queries on multi-value hallmarks field."""
        test_patterns: List[str] = [
            'stem cell exhaustion',
            'DNA instability', 
            'mitochondrial integrity'
        ]
        
        for pattern in test_patterns:
            query = f"""
            SELECT HGNC, "hallmarks of aging"
            FROM gene_hallmarks 
            WHERE "hallmarks of aging" LIKE '%{pattern}%'
            """
            result: QueryResult = opengenes_server.db_query(query)
            
            if result.count > 0:  # Some patterns might not have data
                assert all(pattern in row['hallmarks of aging'] for row in result.rows), \
                    f"All results should contain pattern '{pattern}'"

    def test_intervention_multi_value_search(self, opengenes_server) -> None:
        """Test LIKE queries on intervention multi-value fields."""
        intervention_tests: List[Tuple[str, str]] = [
            ('cardiovascular system', 'intervention_improves'),
            ('nervous system', 'intervention_deteriorates'),
            ('mitochondrial function', 'intervention_improves')
        ]
        
        for pattern, column in intervention_tests:
            query = f"""
            SELECT HGNC, {column}, effect_on_lifespan
            FROM lifespan_change 
            WHERE {column} LIKE '%{pattern}%'
            LIMIT 5
            """
            result: QueryResult = opengenes_server.db_query(query)
            
            if result.count > 0:
                assert all(pattern in (row[column] or '') for row in result.rows), \
                    f"All results should contain pattern '{pattern}' in {column}"

    def test_cross_table_joins(self, opengenes_server) -> None:
        """Test cross-table JOIN operations."""
        query = """
        SELECT DISTINCT lc.HGNC, lc.effect_on_lifespan, la.ethnicity, gc.criteria
        FROM lifespan_change lc
        JOIN longevity_associations la ON lc.HGNC = la.HGNC
        JOIN gene_criteria gc ON lc.HGNC = gc.HGNC
        WHERE lc.effect_on_lifespan = 'increases lifespan'
        LIMIT 5
        """
        result: QueryResult = opengenes_server.db_query(query)
        
        assert result.count > 0, "Should find genes with data across multiple tables"
        
        # Verify all expected columns are present
        expected_columns = ['HGNC', 'effect_on_lifespan', 'ethnicity', 'criteria']
        for row in result.rows:
            for col in expected_columns:
                assert col in row, f"Column '{col}' should be present in results"

    def test_organism_specific_queries(self, opengenes_server) -> None:
        """Test organism-specific filtering."""
        organisms: List[str] = ['mouse', 'roundworm Caenorhabditis elegans', 'fly Drosophila melanogaster']
        
        for organism in organisms:
            query = f"""
            SELECT HGNC, model_organism, effect_on_lifespan
            FROM lifespan_change 
            WHERE model_organism = '{organism}'
            LIMIT 3
            """
            result: QueryResult = opengenes_server.db_query(query)
            
            if result.count > 0:
                assert all(row['model_organism'] == organism for row in result.rows), \
                    f"All results should be for organism '{organism}'"

    def test_enumeration_values_exist(self, opengenes_server) -> None:
        """Test that expected enumeration values exist in the database."""
        enumeration_tests: List[Tuple[str, str, List[str]]] = [
            ('lifespan_change', 'effect_on_lifespan', 
             ['increases lifespan', 'decreases lifespan', 'no change']),
            ('lifespan_change', 'model_organism',
             ['mouse', 'roundworm Caenorhabditis elegans']),
            # Check for any criteria, not specific ones since they may vary
            ('gene_criteria', 'criteria', [])  # Empty list means just check that data exists
        ]
        
        for table, column, expected_values in enumeration_tests:
            query = f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL"
            result: QueryResult = opengenes_server.db_query(query)
            
            actual_values: List[str] = [row[column] for row in result.rows]
            
            # For empty expected_values, just check that we have some data
            if not expected_values:
                assert len(actual_values) > 0, \
                    f"Table {table}.{column} should have some data"
            else:
                # Check if at least some expected values exist
                found_values = [val for val in expected_values if val in actual_values]
                assert len(found_values) > 0, \
                    f"Should find at least some expected values for {table}.{column}. Found: {actual_values[:5]}"

    def test_database_structure(self, opengenes_server) -> None:
        """Test that all expected tables and key columns exist."""
        expected_tables: List[str] = [
            'lifespan_change', 'gene_criteria', 'gene_hallmarks', 'longevity_associations'
        ]
        
        # Test table existence
        result: QueryResult = opengenes_server.db_query("SELECT name FROM sqlite_master WHERE type='table'")
        actual_tables: List[str] = [row['name'] for row in result.rows]
        
        for table in expected_tables:
            assert table in actual_tables, f"Table '{table}' should exist"
        
        # Test key columns exist by querying them
        key_column_tests: List[Tuple[str, str]] = [
            ('gene_hallmarks', '"hallmarks of aging"'),
            ('lifespan_change', 'intervention_improves'),
            ('lifespan_change', 'intervention_deteriorates'),
            ('gene_criteria', 'criteria'),
            ('longevity_associations', 'ethnicity')
        ]
        
        for table, column in key_column_tests:
            query = f"SELECT {column} FROM {table} LIMIT 1"
            result: QueryResult = opengenes_server.db_query(query)
            # Should not raise an exception - column exists

    def test_complex_query_patterns(self, opengenes_server) -> None:
        """Test complex query patterns that LLM agents might use."""
        complex_queries: List[Tuple[str, str]] = [
            ("Genes with multiple criteria", """
                SELECT gc.HGNC, COUNT(DISTINCT gc.criteria) as criteria_count
                FROM gene_criteria gc
                GROUP BY gc.HGNC
                HAVING criteria_count > 1
                LIMIT 5
            """),
            ("Genes with both lifespan effects and hallmarks", """
                SELECT DISTINCT lc.HGNC, lc.effect_on_lifespan, gh."hallmarks of aging"
                FROM lifespan_change lc
                JOIN gene_hallmarks gh ON lc.HGNC = gh.HGNC
                WHERE lc.effect_on_lifespan IN ('increases lifespan', 'decreases lifespan')
                LIMIT 5
            """),
            ("Statistical summary by organism", """
                SELECT model_organism, 
                       COUNT(*) as total_experiments,
                       COUNT(DISTINCT HGNC) as unique_genes
                FROM lifespan_change 
                WHERE model_organism IS NOT NULL
                GROUP BY model_organism
                ORDER BY total_experiments DESC
                LIMIT 5
            """)
        ]
        
        for description, query in complex_queries:
            result: QueryResult = opengenes_server.db_query(query)
            assert result.count >= 0, f"Query should execute without error: {description}"

    def test_multi_value_field_edge_cases(self, opengenes_server) -> None:
        """Test edge cases for multi-value field searches."""
        # Test empty/null handling
        query = """
        SELECT COUNT(*) as null_count
        FROM gene_hallmarks 
        WHERE "hallmarks of aging" IS NULL
        """
        result: QueryResult = opengenes_server.db_query(query)
        null_count: int = result.rows[0]['null_count']
        
        # Test multi-comma handling
        query = """
        SELECT "hallmarks of aging"
        FROM gene_hallmarks 
        WHERE "hallmarks of aging" LIKE '%,%,%'  -- At least 2 commas (3+ values)
        LIMIT 3
        """
        result: QueryResult = opengenes_server.db_query(query)
        
        for row in result.rows:
            hallmarks: str = row['hallmarks of aging']
            comma_count = hallmarks.count(',')
            assert comma_count >= 2, "Should have multiple comma-separated values"


class TestDataIntegrity:
    """Test data integrity and relationships."""

    def test_gene_symbol_consistency(self, opengenes_server) -> None:
        """Test that HGNC gene symbols are consistent across tables."""
        # Get gene symbols from each table
        tables: List[str] = ['lifespan_change', 'gene_criteria', 'gene_hallmarks', 'longevity_associations']
        
        for table in tables:
            query = f"SELECT DISTINCT HGNC FROM {table} WHERE HGNC IS NOT NULL AND HGNC != ''"
            result: QueryResult = opengenes_server.db_query(query)
            
            # Basic validation - should have gene symbols
            assert result.count > 0, f"Table {table} should have gene symbols"
            
            # Gene symbols should be reasonable length (typically 3-10 characters)
            for row in result.rows:
                gene_symbol: str = row['HGNC']
                assert 1 <= len(gene_symbol) <= 20, f"Gene symbol '{gene_symbol}' has unusual length"

    def test_referential_integrity(self, opengenes_server) -> None:
        """Test basic referential integrity between tables."""
        # Find genes that exist in lifespan_change but not in gene_criteria
        query = """
        SELECT COUNT(*) as orphaned_genes
        FROM (
            SELECT DISTINCT HGNC 
            FROM lifespan_change 
            WHERE HGNC IS NOT NULL
        ) lc
        LEFT JOIN (
            SELECT DISTINCT HGNC 
            FROM gene_criteria 
            WHERE HGNC IS NOT NULL
        ) gc ON lc.HGNC = gc.HGNC
        WHERE gc.HGNC IS NULL
        """
        result: QueryResult = opengenes_server.db_query(query)
        orphaned_count: int = result.rows[0]['orphaned_genes']
        
        # Some orphaned genes are expected, but should be reasonable
        total_lc_genes_result: QueryResult = opengenes_server.db_query(
            "SELECT COUNT(DISTINCT HGNC) as total FROM lifespan_change WHERE HGNC IS NOT NULL"
        )
        total_lc_genes: int = total_lc_genes_result.rows[0]['total']
        
        orphaned_ratio: float = orphaned_count / total_lc_genes if total_lc_genes > 0 else 0
        assert orphaned_ratio < 0.8, "Too many genes in lifespan_change missing from gene_criteria"


class TestServerFunctionality:
    """Test the server's built-in functionality."""

    def test_get_schema_info(self, opengenes_server) -> None:
        """Test that get_schema_info returns valid schema information."""
        schema_info = opengenes_server.get_schema_info()
        
        assert isinstance(schema_info, dict), "Schema info should be a dictionary"
        assert 'tables' in schema_info, "Schema info should contain tables"
        assert 'enumerations' in schema_info, "Schema info should contain enumerations"
        
        # Check that expected tables are present
        expected_tables = ['lifespan_change', 'gene_criteria', 'gene_hallmarks', 'longevity_associations']
        for table in expected_tables:
            assert table in schema_info['tables'], f"Table '{table}' should be in schema info"

    def test_get_example_queries(self, opengenes_server) -> None:
        """Test that get_example_queries returns valid examples."""
        examples = opengenes_server.get_example_queries()
        
        assert isinstance(examples, list), "Examples should be a list"
        assert len(examples) > 0, "Should have at least one example query"
        
        for example in examples:
            assert isinstance(example, dict), "Each example should be a dictionary"
            assert 'description' in example, "Each example should have a description"
            assert 'query' in example, "Each example should have a query"
            assert isinstance(example['query'], str), "Query should be a string"
            assert example['query'].strip().upper().startswith('SELECT'), "Query should be a SELECT statement"

    def test_example_queries_execute(self, opengenes_server) -> None:
        """Test that all example queries actually execute without error."""
        examples = opengenes_server.get_example_queries()
        
        for example in examples:
            query = example['query']
            try:
                result: QueryResult = opengenes_server.db_query(query)
                assert result.count >= 0, f"Query should execute: {example['description']}"
            except Exception as e:
                pytest.fail(f"Example query failed: {example['description']}\nQuery: {query}\nError: {e}")


if __name__ == "__main__":
    # Run all tests when executed directly
    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code) 