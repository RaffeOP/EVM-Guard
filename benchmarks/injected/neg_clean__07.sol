pragma solidity 0.8.20;

contract Locker7878 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public deposits;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        total += msg.value;
    }
}
