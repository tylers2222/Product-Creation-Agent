"""Shared resources for the API that need to be accessible across modules"""
import asyncio

queue = asyncio.Queue()

