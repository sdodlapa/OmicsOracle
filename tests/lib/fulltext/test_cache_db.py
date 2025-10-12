"""
Tests for full-text cache database layer.

Tests the FullTextCacheDB class for fast searching and analytics
on cached full-text content.
"""

import tempfile
from pathlib import Path

import pytest

from omics_oracle_v2.lib.fulltext.cache_db import FullTextCacheDB, calculate_file_hash


class TestCacheDBInit:
    """Test database initialization."""
    
    def test_default_initialization(self):
        """Test initialization with default parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = FullTextCacheDB(db_path)
            
            assert db.db_path == db_path
            assert db_path.exists()
            assert db.connection is not None
            
            db.close()
    
    def test_tables_created(self):
        """Test that all required tables are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = FullTextCacheDB(db_path)
            
            cursor = db.connection.cursor()
            
            # Check tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            assert 'cached_files' in tables
            assert 'content_metadata' in tables
            assert 'cache_statistics' in tables
            
            db.close()


class TestCacheDBAddEntry:
    """Test adding entries to database."""
    
    @pytest.fixture
    def db(self):
        """Create a test database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = FullTextCacheDB(Path(tmpdir) / "test.db")
            yield db
            db.close()
    
    def test_add_basic_entry(self, db):
        """Test adding a basic cache entry."""
        success = db.add_entry(
            publication_id='PMC123456',
            file_path='/data/fulltext/pdf/pmc/PMC123456.pdf',
            file_type='pdf',
            file_source='pmc'
        )
        
        assert success is True
        
        # Verify entry was added
        entry = db.get_entry('PMC123456')
        assert entry is not None
        assert entry['publication_id'] == 'PMC123456'
        assert entry['file_type'] == 'pdf'
        assert entry['file_source'] == 'pmc'
    
    def test_add_entry_with_identifiers(self, db):
        """Test adding entry with DOI, PMID, PMC_ID."""
        success = db.add_entry(
            publication_id='PMC123456',
            file_path='/data/test.pdf',
            file_type='pdf',
            file_source='pmc',
            doi='10.1234/test',
            pmid='12345678',
            pmc_id='PMC123456'
        )
        
        assert success is True
        
        entry = db.get_entry('PMC123456')
        assert entry['doi'] == '10.1234/test'
        assert entry['pmid'] == '12345678'
        assert entry['pmc_id'] == 'PMC123456'
    
    def test_add_entry_with_content_metadata(self, db):
        """Test adding entry with content metadata."""
        success = db.add_entry(
            publication_id='PMC123456',
            file_path='/data/test.pdf',
            file_type='pdf',
            file_source='pmc',
            table_count=5,
            figure_count=3,
            section_count=8,
            word_count=5000,
            reference_count=25,
            quality_score=0.95,
            parse_duration_ms=2340
        )
        
        assert success is True
        
        entry = db.get_entry('PMC123456')
        assert entry['table_count'] == 5
        assert entry['figure_count'] == 3
        assert entry['section_count'] == 8
        assert entry['word_count'] == 5000
        assert entry['reference_count'] == 25
        assert entry['quality_score'] == 0.95
        assert entry['parse_duration_ms'] == 2340
        assert entry['has_tables'] == 1  # Boolean true
        assert entry['has_figures'] == 1
    
    def test_update_existing_entry(self, db):
        """Test updating an existing entry."""
        # Add initial entry
        db.add_entry(
            publication_id='PMC123456',
            file_path='/data/test.pdf',
            file_type='pdf',
            file_source='pmc',
            table_count=3
        )
        
        # Update entry
        db.add_entry(
            publication_id='PMC123456',
            file_path='/data/test.pdf',
            file_type='pdf',
            file_source='pmc',
            table_count=5  # Changed
        )
        
        entry = db.get_entry('PMC123456')
        assert entry['table_count'] == 5  # Updated value


class TestCacheDBSearch:
    """Test search functionality."""
    
    @pytest.fixture
    def db(self):
        """Create a test database with sample data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = FullTextCacheDB(Path(tmpdir) / "test.db")
            
            # Add sample entries
            for i in range(10):
                db.add_entry(
                    publication_id=f'PMC_{i}',
                    file_path=f'/data/test_{i}.pdf',
                    file_type='pdf',
                    file_source='pmc' if i % 2 == 0 else 'arxiv',
                    table_count=i,  # 0, 1, 2, ..., 9
                    quality_score=0.9 if i % 2 == 0 else 0.7
                )
            
            yield db
            db.close()
    
    def test_find_papers_with_tables(self, db):
        """Test finding papers with minimum table count."""
        # Find papers with at least 5 tables
        results = db.find_papers_with_tables(min_tables=5)
        
        assert len(results) == 5  # PMC_5 through PMC_9
        assert all(r['table_count'] >= 5 for r in results)
        
        # Results should be ordered by table count DESC
        counts = [r['table_count'] for r in results]
        assert counts == sorted(counts, reverse=True)
    
    def test_find_papers_with_quality_filter(self, db):
        """Test finding papers with quality filter."""
        # Find papers with at least 3 tables and quality >= 0.8
        results = db.find_papers_with_tables(min_tables=3, min_quality=0.8)
        
        # Should only get PMC_4, PMC_6, PMC_8 (even numbers >= 4)
        assert len(results) == 3
        assert all(r['table_count'] >= 3 for r in results)
        assert all(r['quality_score'] >= 0.8 for r in results)
    
    def test_find_papers_with_limit(self, db):
        """Test limiting search results."""
        results = db.find_papers_with_tables(min_tables=1, limit=3)
        
        assert len(results) == 3
        # Should get top 3 by table count (9, 8, 7)
        assert results[0]['table_count'] == 9


class TestCacheDBDeduplication:
    """Test deduplication functionality."""
    
    @pytest.fixture
    def db(self):
        """Create a test database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = FullTextCacheDB(Path(tmpdir) / "test.db")
            yield db
            db.close()
    
    def test_find_by_hash(self, db):
        """Test finding entry by file hash."""
        # Add entry with hash
        file_hash = 'abc123def456'
        db.add_entry(
            publication_id='PMC123456',
            file_path='/data/test.pdf',
            file_type='pdf',
            file_source='pmc',
            file_hash=file_hash
        )
        
        # Find by hash
        result = db.find_by_hash(file_hash)
        
        assert result is not None
        assert result['publication_id'] == 'PMC123456'
        assert result['file_hash'] == file_hash
    
    def test_find_by_hash_not_found(self, db):
        """Test finding non-existent hash."""
        result = db.find_by_hash('nonexistent')
        assert result is None
    
    def test_duplicate_hash_prevention(self, db):
        """Test that duplicate hashes replace existing entries."""
        file_hash = 'abc123'
        
        # Add first entry
        db.add_entry(
            publication_id='PMC111',
            file_path='/data/test1.pdf',
            file_type='pdf',
            file_source='pmc',
            file_hash=file_hash
        )
        
        # Add second entry with same hash (should replace)
        db.add_entry(
            publication_id='PMC222',
            file_path='/data/test2.pdf',
            file_type='pdf',
            file_source='arxiv',
            file_hash=file_hash
        )
        
        # Should only have one entry with this hash
        result = db.find_by_hash(file_hash)
        assert result['publication_id'] == 'PMC222'  # Latest wins


class TestCacheDBStatistics:
    """Test statistics functionality."""
    
    @pytest.fixture
    def db(self):
        """Create a test database with sample data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = FullTextCacheDB(Path(tmpdir) / "test.db")
            
            # Add entries from different sources
            for i in range(5):
                db.add_entry(
                    publication_id=f'PMC_PMC_{i}',
                    file_path=f'/data/pmc/test_{i}.pdf',
                    file_type='pdf',
                    file_source='pmc',
                    file_size_bytes=100000,
                    table_count=i,
                    quality_score=0.95
                )
            
            for i in range(3):
                db.add_entry(
                    publication_id=f'PMC_ARXIV_{i}',
                    file_path=f'/data/arxiv/test_{i}.pdf',
                    file_type='pdf',
                    file_source='arxiv',
                    file_size_bytes=50000,
                    table_count=i * 2,
                    quality_score=0.85
                )
            
            yield db
            db.close()
    
    def test_statistics_by_source(self, db):
        """Test getting statistics grouped by source."""
        stats = db.get_statistics_by_source()
        
        assert 'pmc' in stats
        assert 'arxiv' in stats
        
        # PMC stats
        assert stats['pmc']['count'] == 5
        assert stats['pmc']['avg_quality'] == 0.95
        
        # arXiv stats
        assert stats['arxiv']['count'] == 3
        assert stats['arxiv']['avg_quality'] == 0.85
    
    def test_overall_statistics(self, db):
        """Test getting overall statistics."""
        stats = db.get_overall_statistics()
        
        assert stats['total_entries'] == 8
        assert stats['total_size_mb'] > 0
        assert stats['avg_quality_score'] > 0
        
        # Should have some papers with tables (those with table_count > 0)
        assert stats['papers_with_tables'] > 0


class TestCacheDBMaintenance:
    """Test maintenance operations."""
    
    @pytest.fixture
    def db(self):
        """Create a test database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = FullTextCacheDB(Path(tmpdir) / "test.db")
            yield db
            db.close()
    
    def test_update_access_time(self, db):
        """Test updating last accessed time."""
        # Add entry
        db.add_entry(
            publication_id='PMC123456',
            file_path='/data/test.pdf',
            file_type='pdf',
            file_source='pmc'
        )
        
        # Get initial access time
        entry1 = db.get_entry('PMC123456')
        initial_access = entry1['last_accessed']
        
        # Wait a bit and update
        import time
        time.sleep(0.1)
        db.update_access_time('PMC123456')
        
        # Get updated entry
        entry2 = db.get_entry('PMC123456')
        updated_access = entry2['last_accessed']
        
        # Access time should be updated
        assert updated_access != initial_access
    
    def test_delete_entry(self, db):
        """Test deleting an entry."""
        # Add entry
        db.add_entry(
            publication_id='PMC123456',
            file_path='/data/test.pdf',
            file_type='pdf',
            file_source='pmc',
            table_count=5
        )
        
        # Verify it exists
        assert db.get_entry('PMC123456') is not None
        
        # Delete
        deleted = db.delete_entry('PMC123456')
        assert deleted is True
        
        # Verify it's gone
        assert db.get_entry('PMC123456') is None
    
    def test_delete_nonexistent(self, db):
        """Test deleting non-existent entry."""
        deleted = db.delete_entry('PMC999999')
        assert deleted is False
    
    def test_vacuum(self, db):
        """Test database vacuum operation."""
        # Add and delete some entries to create fragmentation
        for i in range(10):
            db.add_entry(
                publication_id=f'PMC_{i}',
                file_path=f'/data/test_{i}.pdf',
                file_type='pdf',
                file_source='pmc'
            )
        
        for i in range(5):
            db.delete_entry(f'PMC_{i}')
        
        # Vacuum should complete without error
        db.vacuum()


class TestCacheDBContextManager:
    """Test context manager functionality."""
    
    def test_context_manager(self):
        """Test using database as context manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            
            with FullTextCacheDB(db_path) as db:
                db.add_entry(
                    publication_id='PMC123456',
                    file_path='/data/test.pdf',
                    file_type='pdf',
                    file_source='pmc'
                )
                
                entry = db.get_entry('PMC123456')
                assert entry is not None
            
            # Connection should be closed after context
            # (Can't easily test this without accessing private members)


class TestCalculateFileHash:
    """Test file hash calculation."""
    
    def test_calculate_hash(self):
        """Test calculating SHA256 hash of a file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('test content')
            temp_path = Path(f.name)
        
        try:
            hash1 = calculate_file_hash(temp_path)
            
            # Should be valid SHA256 (64 hex characters)
            assert len(hash1) == 64
            assert all(c in '0123456789abcdef' for c in hash1)
            
            # Same file should give same hash
            hash2 = calculate_file_hash(temp_path)
            assert hash1 == hash2
            
        finally:
            temp_path.unlink()
    
    def test_different_files_different_hashes(self):
        """Test that different files produce different hashes."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
            f1.write('content 1')
            path1 = Path(f1.name)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
            f2.write('content 2')
            path2 = Path(f2.name)
        
        try:
            hash1 = calculate_file_hash(path1)
            hash2 = calculate_file_hash(path2)
            
            assert hash1 != hash2
            
        finally:
            path1.unlink()
            path2.unlink()
