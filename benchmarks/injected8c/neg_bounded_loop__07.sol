pragma solidity 0.8.20;

contract Pool1572 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public credit;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        total += msg.value;
    }
    address[] public members;

    function join() public {
        if (members.length < 8) members.push(msg.sender);
    }

    function creditAll() public {
        for (uint256 i = 0; i < 8; i++) {
            if (i < members.length) members[i].code.length;
        }
    }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }

    function totalDeposits() public view returns (uint256) { return total; }
}
