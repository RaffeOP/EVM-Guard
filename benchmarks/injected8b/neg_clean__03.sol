pragma solidity 0.8.20;

contract Fund5170 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public deposits;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        total += msg.value;
    }

    function totalDeposits() public view returns (uint256) { return total; }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
