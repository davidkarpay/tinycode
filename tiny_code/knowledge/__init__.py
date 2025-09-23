"""
TinyCode Knowledge Module

This module provides comprehensive software development principles, code evaluation,
and quality assessment capabilities for the TinyCode AI coding assistant.

Components:
- software_principles: Core software development principles and conventions
- code_evaluator: CodeEvaluator class for analyzing code quality
- Persistent storage for learned patterns and user preferences
"""

from .software_principles import (
    SoftwarePrinciples,
    PrincipleCategory,
    SOLIDPrinciples,
    CleanCodePrinciples,
    TestingPrinciples,
    SecurityPrinciples,
    PerformancePrinciples,
    DocumentationPrinciples,
    VersionControlPrinciples,
    CodeReviewPrinciples,
    RefactoringPrinciples,
    DevOpsPrinciples
)

from .code_evaluator import (
    CodeEvaluator,
    EvaluationResult,
    CodeQualityScore,
    QualityDimension,
    RecommendationType,
    Recommendation
)

__all__ = [
    # Software Principles
    'SoftwarePrinciples',
    'PrincipleCategory',
    'SOLIDPrinciples',
    'CleanCodePrinciples',
    'TestingPrinciples',
    'SecurityPrinciples',
    'PerformancePrinciples',
    'DocumentationPrinciples',
    'VersionControlPrinciples',
    'CodeReviewPrinciples',
    'RefactoringPrinciples',
    'DevOpsPrinciples',

    # Code Evaluator
    'CodeEvaluator',
    'EvaluationResult',
    'CodeQualityScore',
    'QualityDimension',
    'RecommendationType',
    'Recommendation'
]

__version__ = "1.0.0"
__author__ = "TinyCode Team"
__description__ = "Software development principles and code evaluation for TinyCode"